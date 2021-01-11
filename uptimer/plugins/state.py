from collections import OrderedDict

from structlog import get_logger

logger = get_logger()


class PluginState:
    shutdown_order = ("queue", "reader", "writer")
    queue = None
    reader = None
    writer = None

    def __repr__(self):
        return f"<PluginState: {self}>"

    def __str__(self):
        plugins = ", ".join((f"{n}={p}" for n, p in self.plugins.items()))
        return f"{{{plugins}}}"

    def register(self, *, queue=None, reader=None, writer=None):
        if queue:
            self.queue = queue
        if reader:
            self.reader = reader
        if writer:
            self.writer = writer
        logger.info("Registered plugins.", plugins=str(self))

    @property
    def plugins(self):
        return OrderedDict(
            ((plugin, getattr(self, plugin, None)) for plugin in self.shutdown_order)
        )

    def stop(self):
        logger.info(f"Current plugin state: {str(self)}", plugins=str(self))
        for plugin, plugin_instance in self.plugins.items():
            if plugin_instance is not None:
                logger.info(
                    f"Triggering shutdown {plugin}: {plugin_instance}",
                    plugin=plugin,
                    plugin_instance=plugin_instance,
                )
                plugin_instance.stop()
                logger.info(f"Done shutting down {plugin}", plugin=plugin)
            else:
                logger.info(f"Nothing to shut down for plugin: {plugin}", plugin=plugin)


plugin_state = PluginState()
