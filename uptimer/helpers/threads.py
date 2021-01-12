from queue import Empty, Queue
from random import choice
from threading import Event, Thread
from time import sleep

from structlog import get_logger

from uptimer.plugins import ShutdownMarker

logger = get_logger()


class ProcessingThread(Thread):
    """Thread to enable background processing of queued items.

    Example usecase: Whenever a WriterPlugin is processing events in batches, a reader
    returning less events than the batch size, that would cause the writer to block
    indefinitely and not write a shorter batch. The ProcessingThread can subsequently
    be used to implement a timing-out write method in WriterPlugins by wrapping the
    for-loop in a context manager::

        from uptimer.helpers.threads import ProcessingThread
        from uptimer.plugins.writers import WriterPlugin

        class MyBatchWriter(WriterPlugin):
            def write_callback(self, payload):
                # Actually do something with the payload (list of events) here
                self.logger.debug(payload)

            def write(self, payload):
                with ProcessingThread(self.write_callback) as processor:
                    for event in payload:
                        processor.put(event)

    The ProcessingThread expects the first argument to be the callback that should be
    used to write out the data. In practice this means that a writer using the
    ProcessingThread has its writing logic in the callback instead of :meth:`write`.
    """

    _stop_event = Event()
    _data = None

    exception = None
    """Stores exception raised in the thread's activity loop, and its callback."""

    def __init__(self, callback, *, page_size=100, block=True, timeout=5.0, **kwargs):
        """Initializing a ProcessingThread object.

        All arguments given in addition to the ones mentioned below (wrapped up in
        `kwargs` will be forwarded to the callback. This allows additional (static)
        data to be forwarded to the callback. This is useful when the ProcessingThread
        is not initialized in a class context (where `self` isn't available as a method
        of passing data), or when the data can not be made available through the class
        context (for example when wrapped in a context manager).

        Args:
            callback (:obj:`callable`): Method or function to be called when the
                processing thread flushes data from the queue. The callback is expected
                to take *one* positional argument, being a list of objects pulled from
                the processing queue. See :meth:`callback` below for an example
                function signature.
            page_size (int): A value greater zero being the maximum size of one page
                retrieved from the queue. This is the number of objects/events that the
                callback can/should handle when called. Be aware that the callback may
                receive pages shorter than this value, when the queue is flushed
                prematurely.
            block (bool): If retrieving an element from the queue should be blocking
                for :attr:`timeout` seconds. See :obj:`queue.Queue.get` for a more
                detailed description of the behavior.
            timeout (float): For what duration retrieving an element from the queue
                should block when :attr:`block` is `True`. See :obj:`queue.Queue.get`
                for a more detailed description of the behavior.
            kwargs: Any number of *named* arguments to be passed along to the callback
                when executed.
        """

        super().__init__()
        self.callback = callback
        self.page_size = page_size
        self.block = block
        self.timeout = timeout
        self.callback_args = kwargs
        self._data = {}
        self.queue_logger = get_logger()

    def __enter__(self):
        logger.debug("Started processor thread")
        self.start()
        return self

    def __exit__(self, *args, **kwargs):
        logger.debug("Exiting context, stopping thread.")
        self.stop()

    @property
    def stopped(self):
        """Boolean property on the thread's stop event being set.

        It will be True after :meth:`stop` has been called, regardless of the
        processing being completed.
        """
        return self._stop_event.is_set()

    def stop(self):
        """Stops the processing thread, waiting for the queue to be emptied first.

        Stopping the processing thread will first insert a :obj:`ShutdownMarker` at the
        end of the queue and set the thread's stop event. After that the method will
        join the queue and subsequently itself, i.e.: it waits for the queue to be
        emptied completely and the run loop including the callback to be finished
        processing.

        The stop method can be called externally, and will be executed on
        :meth:`__exit__` when the ProcessingThread is used as a context manager.
        """
        logger.debug("Stopping. Will finish processing queue.")
        for _, queue in self._data.items():
            queue.put(ShutdownMarker())
        self.block = False
        self._stop_event.set()
        self.join()

    def put(self, obj, queue_name="main"):
        """Puts an object into the thread's queue.

        Before adding the element to the queue, the method asserts the thread being
        alive and having no previous exception set. If so, the exception is raised in
        the caller's thread.

        Args:
            obj (any): The object that should be added to the queue.
        """
        self._check_liveness()
        if queue_name not in self._data:
            self._data[queue_name] = Queue()

        self._data[queue_name].put(obj)

    def run(self):
        """Method representing the thread’s activity.

        When started the thread will indefinitely pick up pages from the queue (which
        can be fed through :meth:`put`, with a maximum length of :attr:`page_size`. If
        the page is not empty, the callback will be executed.

        Due to limitations in the way exceptions can be raised from a non-main thread.
        an exception occurring during processing will only be raised at the next time
        an object is added to the queue through :meth:`put`.
        """
        try:
            while True:
                page = self._get_page_from_queue()

                if page:
                    logger.debug(
                        f"Current page size: {len(page)} events", page_size=len(page)
                    )
                    if self.callback_args:
                        self.callback(page, **self.callback_args)
                    else:
                        self.callback(page)

                # Only stop processing with signal *and* no queues or all queues empty
                if self.stopped and (
                    len(self._data) == 0
                    or all([q.empty() for _, q in self._data.items()])
                ):
                    logger.debug("Finished processing queue after stop signal")
                    break

        except Exception as e:
            logger.exception("Caught an unexpected exception")
            self.exception = e

    def _get_page_from_queue(self):
        page = []
        if len(self._data) == 0:
            self.queue_logger.debug("No queues present, cannot get page.")
            sleep(0.05)
            return page
        try:
            queue_name, selected_queue = choice(list(self._data.items()))
            self.queue_logger.debug(
                f"Selected queue {queue_name}", queue_name=queue_name
            )

            for _ in range(self.page_size):
                item = selected_queue.get(block=self.block, timeout=self.timeout)
                selected_queue.task_done()
                if isinstance(item, ShutdownMarker):
                    logger.debug("Received shutdown marker")
                    self._stop_event.set()
                    del self._data[queue_name]
                    return page

                page.append(item)

        except Empty:
            pass
        return page

    def _check_liveness(self):
        if not self.is_alive():
            logger.error("Processing thread not alive.")
        if self.exception:
            raise self.exception

    def callback(self, page, **kwargs):
        """Method getting called when the thread is flushing the queue.

        Note:
            This particular implementation of a callback is not used when instantiating
            a ProcessingThread object, as it is overloaded on :meth:`__init__`. It may
            only be used for illustrating the how the thread works.

        Args:
            page (list): List of items retrieved from the queue of the thread, either
                after reaching the timeout, or when its length has reached
                :attr:`page_size`.
            kwargs: An arbitrary array of *named* arguments passed along from
                :attr:`kwargs` on :meth:`__init__`.

        """
