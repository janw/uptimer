from abc import abstractmethod
from typing import ClassVar, Iterator

from uptimer.events import Event
from uptimer.plugins import BasePlugin

# Note:
# - All readers generating an initial event should get a UUID and put it in the event.
# - If reading something, it shouĺd be implicit that an id is provided.


class ReaderPlugin(BasePlugin):
    """Abstract Base Class for reader plugins in uptimer.

    All reader plugins in uptimer must implement the :meth:`read` and
    :meth:`dummy_read` methods, that get called in the main application loop. When
    uptimer is running dummy data mode (by setting the :data:`DUMMY_DATA`
    environment variable / setting), the `dummy_read` method will be called instead of
    the `read` method.

    Plugin developers are asked to develop `read` and `dummy_read` in close conjuction
    with one another. `dummy_read`'s purpose is to output fake data that closely
    resembles the "real" data output by `read` so that uptimer can run all plugins
    in an enclosed environment that does not allow connections to external data
    sources. This is especially useful for end-to-end tests before deployment.
    """

    def __init__(self, *args, **kwargs):
        """Instantiates a ReaderPlugin.

        Inheriting from :class:`uptimer.events.base.Event` gives the class its own
        :attr:logger. When the :data:`DUMMY_DATA` setting is set, :meth:`__init__` will
        overload :meth:`read` with :meth:`dummy_read`.

        Plugin developers should always prefix their reimplementations with::

            super().__init__(*args, **kwargs)

        """

        # Append `dummy_data` to optional_settings before super init
        # (which does the PluginSettings handling).
        if "dummy_data" not in self.optional_settings:
            self.optional_settings += ("dummy_data",)

        super().__init__(*args, **kwargs)
        if self.settings.dummy_data or False:
            self.logger.warning("Running reader in dummy data mode.")
            self._read = self.read
            self.read = self.dummy_read

    @abstractmethod
    def read(self) -> Iterator[Event]:
        # ABC inherently raises TypeError for unimplemented methods
        pass  # pragma: no cover

    @property
    @abstractmethod
    def event_type(self):
        """Event type the reader plugin is expected to yield.

        The event type is used for generating dummy events (with fake data) and might
        be used to add additional validation in the future.
        """
        pass  # pragma: no cover

    def dummy_read(self) -> Iterator[Event]:
        """Returns an iterator for dummy instances of the plugin's event_type.

        All plugins are required to declare their :attr:`event_type` to be able to
        return a dummy event generator here. Event types inheriting from the base Event
        class inherit the :meth:`uptimer.events.base.Event.dummy_instances` method,
        that yields dummy events of their type.

        Returns:
            :obj:`iter`: Yield of `dummy_instances` from the plugin's set
            :attr:`event_type`.

        """
        return self.event_type.dummy_instances()

    is_one_shot_reader: ClassVar[bool] = True
