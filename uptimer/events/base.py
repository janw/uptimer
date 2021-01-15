import json
from collections.abc import MutableMapping
from datetime import datetime, timezone
from typing import Any, ClassVar, Optional
from uuid import UUID, uuid4

import jsonschema
from structlog import get_logger

from uptimer.events import DEFAULT_TABLE, ROOT_SCHEMA
from uptimer.events.formats import JSONEncoder, format_checker
from uptimer.events.meta import EventMeta
from uptimer.exceptions import ValidationError

logger = get_logger()


class Event(MutableMapping, metaclass=EventMeta):
    """Base class for uptimer events.

    Implements interfaces to have arbitrary input validated against a given JSON
    schema specification. The schema defaults to the root schema (set in
    :const:`uptimer.events.ROOT_SCHEMA` within the event module) in
    :file:`uptimer/events/schemata/root.json`. Subclassing Event allows
    implementing custom event types by declaring the `schema`, and `table` class
    variables::

        from uptimer.events import Event

        class MyCustomEvent(Event):
            schema = "my-custom-event.json"
            table = "my_custom_event_table"

    All JSON schemas in uptimer must contain the following statements,
    inheriting all properties and schema requirements from the ``ROOT_SCHEMA``::

        {
            "$schema": "http://json-schema.org/draft-07/schema",
            "title": "Example Data Schema",
            "version": "0.1.0",
            "type": "object",
            "allOf": [
                {
                    "$ref": "root.json"
                },
                {
                    "properties": {
                    },
                    "required": []
                }
            ]
        }
    """

    schema: ClassVar[str] = ROOT_SCHEMA
    """Filename of the JSON schema to load."""

    table: ClassVar[Optional[str]] = DEFAULT_TABLE
    """Database table mapping."""

    schema_spec: ClassVar[dict]
    """Loaded JSON schema specification (derived from `schema`)."""

    properties_dict: ClassVar[dict]
    """Properties of the loaded JSON schema."""

    def __init__(
        self,
        *,
        uuid: Optional[UUID] = None,
        event_time: Optional[datetime] = None,
        validate: Optional[bool] = True,
        **kwargs: Any,
    ) -> None:
        """Instantiates an Event with the given input parameters as its initial state.

        Args:
            uuid (str): UUID of the event. If ``None``, a UUID will be generated
                automatically.
            event_time (str): Timestamp of the event. Must be in date-time format as
                specified by `RFC3339`_.
            validate (bool): Set to false to prevent the event state from being
                validated on creation.

        .. _`RFC3339`: https://tools.ietf.org/html/rfc3339#section-5.6
        """
        self._data: dict = dict()
        self.update(
            {
                "schema_title": self.schema_spec["title"],
                "schema_version": self.schema_spec["version"],
                "uuid": uuid or uuid4(),
                "event_time": datetime.now(timezone.utc)
                if event_time is None
                else event_time,
                **kwargs,
            }
        )
        for schema_property, subschema in self.properties_dict.items():
            if "default" in subschema:
                self.setdefault(schema_property, subschema["default"])
        if validate:
            self.validate()

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return f"<{self.__class__.__name__} {repr(self._data)}>"

    @property
    def naive_repr(self):
        return json.loads(self.to_json(validate=False))

    def validate(self):
        """Validate the event's data against its JSON schema.

        Returns:
            None

        Raises:
            ValidationError: If the validation of the event data fails.
        """
        try:
            jsonschema.validate(
                instance=self.naive_repr,
                schema=self.schema_spec,
                resolver=self._resolver,
                format_checker=format_checker,
            )
        except Exception:
            logger.exception(
                "Encountered exception during validation",
                offending_event=self.naive_repr,
            )
            raise

    @classmethod
    def from_json(cls, data):
        """Instantiates a class object from a given JSON object or string.

        Args:
            data (dict or str): JSON object, or string to be parsed into a JSON object.

        Returns:
            Event: Event object with the input data as its state.
        Raises:
            ValueError: when `data` is neither a JSON object nor parsable to one.
        """
        if isinstance(data, str):
            data = json.loads(data)
        if not isinstance(data, dict):
            raise ValueError("Input must be JSON object (or python-native dict)")

        return cls.from_uncast_dict(data)

    @classmethod
    def from_uncast_dict(cls, data):
        """Instantiates a class object from a given dict of uncast values.

        When an event is written to a plain-text destination (e.g. a CSV file), the
        typing of its properties is not preserved. This classmethod allows to re-read
        events from such locations, auto-detecting the data's typing based on the Event
        type's JSON schema.

        Success or failure of this detection is determined when instantiating the Event
        object, by validating the future object against the schema.

        Args:
            data (dict): Dict of string values to be parsed into the class object

        Returns:
            Event: Event object with the input data as its state.
        Raises:
            ValidationError: If the validation of the data fails.
        """
        cast_data = data.copy()
        for key, value in cast_data.items():
            callables = cls.property_cast_mapping.get(key, None)

            # When the event has additional data that is not present in the JSON
            # schema, there won't be an entry in the cast mapping for it. Therefore
            # we cannot entirely load the event from the given JSON payload and have
            # to fail.
            if callables is None:
                raise ValidationError(
                    f"Property '{key}' is invalid for events of type {cls.__name__} "
                )

            if not isinstance(value, str):
                continue
            for cast in callables:
                try:
                    cast_data[key] = cast(value)
                except ValueError:
                    continue

        return cls(**cast_data)

    def to_json(self, *, validate=False, **kwargs):
        """Validates the Event and serializes it to a JSON formatted string.

        Args:
            validate (bool): True to perform the validation before serialization,
                False otherwise.
            **kwargs: Arbitrary keyword arguments, passed on to :func:`json.dumps`.

        Returns:
            str: The serialized JSON formatted representation of the Event.

        """
        if validate:
            self.validate()
        return json.dumps(self._data, cls=JSONEncoder, **kwargs)

    @classmethod
    def dummy_instances(cls, max_count=None):
        """Yields Event class instances with randomly generated dummy data.

        Returns:
            generator: Generator for single instances of the class populated with dummy
                data.

        """
        dummy = cls.DummyData()
        for data in dummy.generate():
            yield cls(validate=False, **data)

    class DummyData:
        MAX_COUNT = 1000

        def generate(self):
            raise NotImplementedError(
                "DummyData not implemented."
                " Add a subclass DummyData to your event type or"
                " override the dummy_read method of your plugin."
            )

            for _ in range(self.MAX_COUNT):
                yield {}
