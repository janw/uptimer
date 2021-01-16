import logging.config
from os import path

import structlog
import yaml

from uptimer import ROOT_PATH
from uptimer.core import settings


def load_config():
    with open(path.join(ROOT_PATH, "core", "logging.yaml"), "r") as config_yaml:
        return yaml.load(config_yaml, Loader=yaml.SafeLoader)


OVERRIDES_CONFIG = load_config()


DEFAULT_PROCESSORS = [
    structlog.processors.StackInfoRenderer(),
    structlog.dev.set_exc_info,
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.processors.format_exc_info,
    structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M.%SZ", utc=True),
    structlog.processors.UnicodeDecoder(),
]


def setup_logging():
    """Sets up logging through structlog.

    The entirety of logging output from uptimer is issued through :mod:`structlog`.
    Dependent on the working environment uptimer is run in, the final rendering of the
    log output is adjusted:

    * The `development` environment uses :class:`structlog.dev.ConsoleRenderer` for
        pretty, colorized, human-readable log messages
    * All other environments use :class:`structlog.processors.JSONRenderer` to output
        easily parseable JSON. This is useful for both parsing the output in
        `production` using external tools such as Fluentd or Logstash, as well as in
        `testing` by loading the JSON and ensuring the expected contents are getting
        logged.
    """
    processors = DEFAULT_PROCESSORS
    if settings.current_env.lower() == "development":  # pragma: no cover
        pad_event = int(settings.get("DEVELOPMENT_PAD_EVENT", "50"))
        processors += [structlog.dev.ConsoleRenderer(pad_event=pad_event, colors=True)]
    else:
        processors += [structlog.processors.JSONRenderer()]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,  # Prevents wrong plugin logger __name__
    )

    if "LOG_LEVEL" in settings:
        logging.root.setLevel(settings.LOG_LEVEL.upper())
    if "UPTIMER_LOG_LEVEL" in settings:
        logging.getLogger("uptimer").setLevel(settings.UPTIMER_LOG_LEVEL.upper())

    # Stdlib logging config for level overrides, and message-only output
    logging.config.dictConfig(OVERRIDES_CONFIG)
    logging.basicConfig(format="%(message)s")
