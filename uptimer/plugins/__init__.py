from abc import ABC
from importlib import import_module
from inspect import isclass
from typing import Any, ClassVar, Dict, Mapping, Optional, Tuple, Type, TypeVar, Union

from structlog import get_logger

from uptimer.core import settings as dynaconf_settings
from uptimer.events.base import Event
from uptimer.plugins.settings import PluginSettings

DEFAULT_PLUGIN_CLASSNAME = "Plugin"

logger = get_logger()


class BasePlugin(ABC):
    """Abstract base class to inherit all uptimer plugins from.

    Plugins are set up with their own :mod:`logger`, and allow automatic validation
    of required settings through :mod:`uptimer.settings`. All plugins have to
    implement :attr:`plugin_type`.
    """

    required_settings: ClassVar[Tuple[str, ...]] = ()
    """Tuple of settings required for the plugin to run.

    The settings will be parsed from environment variables and instance arguments, and
    from :prop:`required_settings` and :prop:`optional_settings`. They will then be
    merged into the :prop:`settings` variable. If a setting exists in both env vars and
    arguments, arguments take precedence. A setting cannot be present in both
    :prop:`required_settings` and :prop:`optional_settings`.

    The variable must be set as a class variable (cannot be modified during runtime),
    and can only contain lower-case strings with alphanumeric characters and
    underscores.
    """

    optional_settings: ClassVar[Tuple[str, ...]] = ()
    """Tuple of optional plugin settings.

    If a setting is not provided at runtime, it will be none in :prop:`settings`.
    Otherwise `optional_settings` behaves like :prop:`required_settings`, see it for
    more details.
    """

    def __init__(self, *args, **kwargs) -> None:
        # Give plugins their own logger
        class_name = f"{self.__class__.__module__}.{self.__class__.__qualname__}"
        self.logger = get_logger()
        self.logger.debug(f"Initializing plugin {class_name}", class_name=class_name)

        self.settings = PluginSettings(
            required=tuple(map(lambda x: x.lower(), self.required_settings)),
            optional=tuple(map(lambda x: x.lower(), self.optional_settings)),
            # Sources must be given in order of precedence
            sources=(dynaconf_settings, kwargs),
        )

        super().__init__(*args)

    event_type: Type[Event] = Event
    """Event type the plugin is expected to handle.

    For plugins inheriting from :class:`uptimer.plugins.readers.ReaderPlugin`
    that is the expected event type for the Plugin to yield, and from which dummy
    events (with fake data) are created. For plugins inheriting from
    :class:`uptimer.plugins.readers.WriterPlugin`, that is the event type to
    validate incoming events against.
    """

    def __str__(self):
        modstr = self.__class__.__module__
        if modstr.startswith("uptimer.plugins."):
            modstr = modstr[20:]
        return modstr

    def __repr__(self):
        return f"Plugin({self})"

    def stop(self) -> None:
        """Signalling method called when uptimer gets shut down.

        This method will most likely be called when a SIGTERM is received.
        Implement it to flush left-over data that should not be lost.
        """
        pass


class ShutdownMarker:
    """Signalling class to mark end of input

    The ShutdownMarker should be put in queues (or similar) when you want to
    show that you shouldn't wait for any further input.
    """

    pass


def resolve_entrypoint(entrypoint: str) -> Tuple[str, str]:
    """Resolve a given entrypoint into module and class name.

    If no class name has been given (separated by a colon), the
    `DEFAULT_PLUGIN_CLASSNAME` name will be used. For example

    plugins.readers.random_cat_fact:CatFact

    resolves to the importable module `plugins.readers.random_cat_fact`
    with the class name being `CatFact`.

    """
    splits = entrypoint.split(":")
    split_count = len(splits)

    if split_count == 2:
        return splits[0], splits[1]
    elif split_count == 1:
        return splits[0], DEFAULT_PLUGIN_CLASSNAME
    else:
        raise ValueError("Cannot parse entrypoint definition")


Plugin = TypeVar("Plugin", bound=BasePlugin)


def load_plugin(
    entrypoint: Union[str, Dict[str, Any], Type[Plugin]],
    *,
    parameters: Optional[dict] = None,
) -> Plugin:
    """Load an instance of a plugin from the given plugin configuration.

    Expects input parameter to either be an entrypoint string, a dict containing an
    `entrypoint` string, or a class inheriting from BasePlugin. The `entrypoint` string
    has to contain an importable module name, and an optional `:<class name>` separated
    by a colon. If the `:suffix` is not present, the default plugin class name from
    :var:`DEFAULT_PLUGIN_CLASSNAME` will be used.
    """
    parameters = parameters or {}
    if isinstance(entrypoint, dict):
        if "entrypoint" not in entrypoint:
            raise ValueError("Missing `entrypoint` key in dict-type argument")
        entrypoint_string = entrypoint["entrypoint"]
        parameters.update(entrypoint.get("parameters", {}))
    elif isinstance(entrypoint, str):
        entrypoint_string = entrypoint
    elif isclass(entrypoint) and issubclass(entrypoint, BasePlugin):
        return entrypoint(**parameters)
    else:
        raise ValueError("Missing entrypoint in plugin configuration")

    modulename, classname = resolve_entrypoint(entrypoint_string)
    try:
        module = import_module(modulename)
    except ModuleNotFoundError:
        module = import_module(f"{__name__}.{modulename}")

    return getattr(module, classname)(**parameters)
