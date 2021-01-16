import signal

from structlog import get_logger

from uptimer.plugins.state import plugin_state

logger = get_logger()


def sigterm_handler(signal_number, frame):  # pragma: no cover
    logger.info("Received SIGTERM. Calling stop() on plugin state.", signal="SIGTERM")
    plugin_state.stop()


def register_handlers():
    logger.debug("Registering signal handlers")
    signal.signal(signal.SIGTERM, sigterm_handler)
