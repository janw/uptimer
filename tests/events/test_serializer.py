from datetime import datetime
from uuid import UUID

import pytest

from uptimer.events import Event
from uptimer.events.serializer import dumps, loads

FIXTURE_SERIALIZED = """
{
  "uuid": "0e436b7c-4814-46ec-bcbc-3884060f735b",
  "event_time": "2020-02-21T11:56:52.399558+00:00",
  "schema_title": "DummyEvent",
  "schema_version": "0.1.0",
  "target": "nowhere",
  "reader": "readers.dummies.dummy_events",
  "integer_value": 42,
  "float_value": 13.37
}
"""

FIXTURE_SERIALIZED_INCOMPLETE = """
{
  "target": "nowhere",
  "reader": "readers.dummies.dummy_events",
  "integer_value": 42,
  "float_value": 13.37
}
"""


def test_serializer_loads():

    event = loads(FIXTURE_SERIALIZED)

    assert isinstance(event["event_time"], datetime)
    assert isinstance(event["uuid"], UUID)
    assert isinstance(event["integer_value"], int)
    assert isinstance(event["float_value"], float)


def test_serializer_loads_error():
    with pytest.raises(ValueError):
        loads(FIXTURE_SERIALIZED_INCOMPLETE)


def test_serializer_dumps():
    event = Event()
    dumped_event = dumps(event)
    reloaded_event = loads(dumped_event)

    assert isinstance(dumped_event, bytes)
    assert isinstance(event, Event)
    assert event == reloaded_event
