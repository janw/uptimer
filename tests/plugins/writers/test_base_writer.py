import pytest

from uptimer.events import Event
from uptimer.events.stubs import DummyEvent
from uptimer.exceptions import ValidationError
from uptimer.plugins.writers import WriterPlugin

event = Event(something="something")
dummy = DummyEvent(
    target="this",
    reader="that",
    integer_value=42,
    float_value=13.37,
)


class ConcreteTestClass(WriterPlugin):
    plugin_type = "Concrete Test Implemetation of a Writer Plugin"

    def write(self):
        pass


writer = ConcreteTestClass()


def test_validate_event_type():
    output = writer.validate_event_type(event)

    assert output is event
    with pytest.raises(ValidationError):
        writer.validate_event_type(dummy)
    writer.validate_event_type(dummy, strict=False)
    with pytest.raises(ValidationError):
        writer.validate_event_type(dict(), strict=False)


def test_validate_event_type_to_json():
    expected = (
        '"target": "this"',
        '"reader": "that"',
        '"integer_value": 42',
        '"float_value": 13.37',
    )
    output = writer.validate_event_type(dummy, strict=False, to_json=True)

    # Iterate over snippets since order in the JSON string is not deterministic.
    for snippet in expected:
        assert snippet in output


def test_validate_event_type_to_tuple():
    keys = ("float_value", "target")
    expected = (13.37, "this")
    output = writer.validate_event_type(dummy, strict=False, to_tuple_by_keys=keys)

    assert isinstance(output, tuple)
    assert len(output) == 2
    assert output == expected


def test_validate_event_type_to_tuple_with_missing_keys():
    keys = ("float_value", "target", "nonexistent_key")

    with pytest.raises(KeyError):
        writer.validate_event_type(dummy, strict=False, to_tuple_by_keys=keys)


def test_validate_event_type_to_tuple_with_missing_keys_ignored():
    keys = ("float_value", "target", "nonexistent_key")
    expected = (13.37, "this", None)

    output = writer.validate_event_type(
        dummy, strict=False, to_tuple_by_keys=keys, ignore_missing_keys=True
    )

    assert isinstance(output, tuple)
    assert len(output) == 3
    assert output == expected


def test_validate_event_type_mutually_exclusive_params():
    with pytest.raises(ValueError):
        writer.validate_event_type(
            dummy, strict=False, to_json=True, to_tuple_by_keys=("something")
        )
