from abc import abstractmethod
from typing import ClassVar, Iterator

from uptimer.events import Event
from uptimer.plugins import BasePlugin


class ReaderPlugin(BasePlugin):
    """Abstract Base Class for reader plugins in uptimer.

    All reader plugins in uptimer must implement the :meth:`read` method, that get
    called in the main application loop.
    """

    @abstractmethod
    def read(self) -> Iterator[Event]:
        # ABC inherently raises TypeError for unimplemented methods
        pass  # pragma: no cover

    @property
    @abstractmethod
    def event_type(self):
        """Event type the reader plugin is expected to yield.

        The event type might be used to add additional validation in the future.
        """
        pass  # pragma: no cover

    is_one_shot_reader: ClassVar[bool] = True
