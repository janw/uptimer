import os
from datetime import datetime

from structlog import get_logger

from uptimer.core import settings
from uptimer.core.handlers import register_handlers
from uptimer.core.processors import queue_processor, static_reader_writer_processor
from uptimer.plugins import load_plugin


def main():
    logger = get_logger()
    logger.info(
        "Starting uptimer",
        starttime=datetime.now().isoformat(),
        env=settings.ENV_FOR_DYNACONF,
    )
    register_handlers()
    try:
        writer = load_plugin(settings.WRITER_PLUGIN)

        if settings.get("QUEUE_PLUGIN"):
            queue_processor(writer, settings.QUEUE_PLUGIN)
        else:
            static_reader_writer_processor(writer, settings.READER_PLUGIN)
    except Exception:  # pragma: no cover
        logger.exception("Caught exception in main. Exiting.", exc_info=True)
        os._exit(1)
