import time

from structlog import get_logger

from uptimer.plugins import load_plugin
from uptimer.plugins.state import plugin_state

logger = get_logger()


def queue_processor(writer, queue_plugin):
    queue = load_plugin(queue_plugin)
    plugin_state.register(queue=queue)

    logger.info("Entering queue processing loop.")
    for job in queue.read():
        start_time = time.time()
        if job.is_expired:
            logger.info(
                "Discarding expired queue entry",
                uuid=str(job["uuid"]),
                reader=job["reader"],
            )
            continue

        reader = load_plugin(job["reader"], parameters=job.get("parameters", None))
        plugin_state.register(queue=queue, reader=reader, writer=writer)
        logger.info(
            "Will process queue entry.", uuid=str(job["uuid"]), reader=job["reader"]
        )

        writer.write(reader.read())

        stop_time = time.time()
        duration = stop_time - start_time

        logger.info(
            "Finished processing queue entry.",
            uuid=str(job["uuid"]),
            reader=job["reader"],
            duration=duration,
        )


def static_reader_writer_processor(writer, reader_plugin):
    reader = load_plugin(reader_plugin)
    plugin_state.register(reader=reader, writer=writer)

    logger.info("Entering read/write loop.")
    while True:
        writer.write(reader.read())

        if reader.is_one_shot_reader:
            break
