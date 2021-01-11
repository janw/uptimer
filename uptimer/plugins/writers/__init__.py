from abc import abstractmethod

from uptimer.events.base import Event
from uptimer.exceptions import ValidationError
from uptimer.plugins import BasePlugin


class WriterPlugin(BasePlugin):
    """Abstract base class for writer plugins.

    All classes inheriting from WriterPlugin are required to implement the
    :meth:`write` method, and the :attr:`plugin_type` attribute inherited from the
    `BasePlugin`.
    """

    event_type = Event
    """Event type to validate the given payload data against."""

    @abstractmethod
    def write(self, payload):
        # ABC inherently raises TypeError for unimplemented methods
        pass  # pragma: no cover

    @classmethod
    def validate_event_type(
        cls,
        event,
        strict=True,
        to_json=False,
        to_tuple_by_keys=None,
        ignore_missing_keys=False,
    ):
        """Validates the payload's event type against :attr:`event_type`.

        Can perform optional transformations on the given Event for output (for example
        to use in a processing loop). The output type is selected by the `to_json` and
        `to_tuple_by_keys` parameters.

        Args:
            event (:obj:`Event`): Event for the method to validate against the event
                type
            strict (bool): If True (default) the Payload's events must be instances
                :attr:`event_type`. If False, the Payload's event type must be a
                subclass of :class:`uptimer.events.Event`.
            to_json (bool): If True returns the output of the Event's `to_json` method.
            to_tuple_by_keys (:obj:`iter`): Iterable by which to unpack the Event into a
                tuple. The iterable's ordering is kept intact so that the tuple has a
                dependable property order.

        Returns:
            :obj:`Event`, :obj:`str`, or :obj:`tuple`:
                An unmodified :obj:`Event` from the input parameter if `to_json` is
                False.

                The Event's JSON-serialized :obj:`str` representation if `to_json` is
                True.

                A :obj:`tuple` of the Event's properties keyed by `to_tuple_by_keys`
                iterable.

        Raises:
            :class:`uptimer.exceptions.ValidationError`: when validation criteria
                are not met (i.e. either not subclass of
                :class:`uptimer.events.Event` or instance of :attr:`event_type`.)
            ValueError: when `to_json` and `to_tuple_by_keys` are both passed to the
                method (they are mutually exclusive).
        """
        if type(event) is not cls.event_type and strict:
            raise ValidationError(
                f"Input data is not {cls.event_type}: {event} ({type(event)})"
            )
        elif not isinstance(event, Event):
            raise ValidationError(
                f"Input data is not an Event subclass: {event} ({type(event)})"
            )

        if to_json and to_tuple_by_keys:
            raise ValueError(
                "Params to_json and to_tuple_by_keys are mutually exclusive."
            )

        if to_json:
            return event.to_json()
        elif to_tuple_by_keys:
            if ignore_missing_keys:
                return tuple(event.get(key, None) for key in to_tuple_by_keys)
            else:
                return tuple(event[key] for key in to_tuple_by_keys)
        return event
