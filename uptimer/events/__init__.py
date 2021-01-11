from os import path

ROOT_SCHEMA: str = "root.json"
"""The default root JSON schema to be used for all event (sub)classes."""

SCHEMATA_SUBDIR: str = "schemata"
"""Directory from where all relative paths to JSON schemata are tried first."""

HERE: str = path.dirname(path.realpath(__file__))
SCHEMATA_PATH: str = path.join(HERE, SCHEMATA_SUBDIR, "")
ROOT_SCHEMA_FULLPATH: str = path.join(SCHEMATA_PATH, ROOT_SCHEMA)
DEFAULT_TABLE: str = "event"

from uptimer.events.base import Event  # noqa: F401, E402
from uptimer.events.stubs import *  # noqa: F401, E402, F403
