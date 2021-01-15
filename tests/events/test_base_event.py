from datetime import datetime
from json import JSONDecodeError
from uuid import UUID as uuid

import pytest
from jsonschema import ValidationError

from tests.events.event_fixtures import DoublyNestedEvent, SimpleEvent, TypecastingEvent
from uptimer.events import Event
from uptimer.events.meta import EventDefinitionError


def test_concrete_event_class():
    testevent = Event()

    assert isinstance(testevent["schema_title"], str)
    assert isinstance(testevent["schema_version"], str)
    assert isinstance(testevent["uuid"], uuid)
    assert isinstance(testevent["event_time"], datetime)


def test_properties_method():
    testevent = Event()

    assert len(testevent.properties) == 4
    for elem in ("uuid", "schema_title", "event_time", "schema_version"):
        assert elem in testevent.properties


def test_nested_schema_properties():
    expected_properties = [
        "uuid",
        "schema_version",
        "schema_title",
        "event_time",
        "protocol",
        "hostname",
        "port",
        "path",
        "status_code",
        "response_time_ms",
        "error",
        "regex",
        "matches_regex",
        "customer",
        "cool_thing",
        "something_nested",
    ]

    dn = DoublyNestedEvent(validate=False)  # Do not validate for empty event

    assert len(dn.properties) == len(expected_properties)
    for elem in dn.properties:
        assert elem in expected_properties


def test_to_json():
    testevent = Event(
        event_time="2019-04-10T12:43:05.200947+00:00",
        uuid="52c76d2c-514f-49ba-b8f7-09065b214e95",
    )
    expected_output = (
        '{"schema_title": "Event", "schema_version": "0.1.0", '
        '"uuid": "52c76d2c-514f-49ba-b8f7-09065b214e95", '
        '"event_time": "2019-04-10T12:43:05.200947+00:00"}'
    )
    expected_repr = f"<Event {expected_output}>".replace('"', "'")

    output_to_json = testevent.to_json()
    output_repr = repr(testevent)

    assert output_to_json == expected_output
    assert output_repr == expected_repr


def test_datetime_validation():
    with pytest.raises(ValidationError):
        Event(event_time="boat", uuid="52c76d2c-514f-49ba-b8f7-09065b214e95")


def test_collection_methods():
    testevent = Event()
    keys = ["uuid", "event_time", "schema_title", "schema_version"]

    # Tests for __iter__
    for key in testevent:
        assert key in keys

    # Tests for __len__
    assert len(testevent) == len(keys)


def test_missing_required_property():
    testevent = Event(
        validate=False,  # Disable validation on __init__, done further down
        event_time="2019-04-10T12:43:05.200947+00:00",
        uuid="52c76d2c-514f-49ba-b8f7-09065b214e95",
    )
    del testevent["uuid"]

    with pytest.raises(ValidationError):
        testevent.validate()


def test_from_json():
    json_str = (
        '{"uuid": "52c76d2c-514f-49ba-b8f7-09065b214e95", '
        '"event_time": "2019-04-10T12:43:05.200947+00:00", '
        '"schema_title": "Base Event", "schema_version": "0.1.0"}'
    )
    json_obj = {
        "uuid": "52c76d2c-514f-49ba-b8f7-09065b214e95",
        "event_time": "2019-04-10T12:43:05.200947+00:00",
        "schema_title": "Base Event",
        "schema_version": "0.1.0",
    }

    event_from_str = Event.from_json(json_str)
    event_from_obj = Event.from_json(json_obj)

    assert isinstance(event_from_str, Event)
    assert isinstance(event_from_obj, Event)


@pytest.mark.parametrize(
    "instance", [(list()), (int(1)), (float(1.1))], ids=["list", "int", "float"]
)
def test_from_json_wrong_type(instance):
    with pytest.raises(ValueError):
        Event.from_json(instance)


@pytest.mark.parametrize(
    "instance",
    [
        (
            {
                "uuid": "Nope, not a uuid",
                "event_time": "2019-04-10T12:43:05.200947+00:00",
                "schema_title": "Base Event",
                "schema_version": "0.1.0",
            }
        ),
        (
            {
                "uuid": "52c76d2c-514f-49ba-b8f7-09065b214e95",
                "event_time": "This is not the date you are looking for",
                "schema_title": "Base Event",
                "schema_version": "0.1.0",
            }
        ),
    ],
    ids=["uuid", "event_time"],
)
def test_from_json_wrong_property_format(instance):
    with pytest.raises(ValidationError):
        Event.from_json(instance)


def test_from_json_invalid_object():
    with pytest.raises(JSONDecodeError):
        Event.from_json("invalid json")


@pytest.mark.parametrize(
    "instance",
    [
        (
            {
                "int_number": "42",
                "int_or_null": "77",
                "float_number": "14.91",
                "bouillon": "true",
                "string_uuid": "52c76d2c-514f-49ba-b8f7-09065b214e95",
                "string_date": "Sat Oct 11 17:13:46 UTC 2003",
            }
        ),
        (
            {
                "int_number": "42",
                "int_or_null": "null",
                "float_number": "14.91",
                "bouillon": "false",
                "string_uuid": "52c76d2c-514f-49ba-b8f7-09065b214e95",
                "string_date": "19970902T090000",
            }
        ),
        (
            {
                "int_number": "42",
                "int_or_null": "null",
                "float_number": "17",
                "bouillon": "false",
                "string_uuid": "52c76d2c-514f-49ba-b8f7-09065b214e95",
                "string_date": "March 12, 1991",
            }
        ),
    ],
    ids=["int", "int_or_null", "float"],
)
def test_from_uncast_dict(instance):
    event = TypecastingEvent.from_uncast_dict(instance)
    assert isinstance(event["int_number"], int)
    assert isinstance(event["int_or_null"], int) or event["int_or_null"] is None
    assert isinstance(event["float_number"], float)
    assert isinstance(event["bouillon"], bool)
    assert isinstance(event["string_uuid"], uuid)
    assert isinstance(event["string_date"], datetime)


@pytest.mark.parametrize(
    "instance",
    [
        (
            {
                "int_number": "42",
                "int_or_null": "77",
                "float_number": "14.91",
                "bouillon": "true",
                "string_uuid": "technically a string but not a uuid",
            }
        ),
        (
            {
                "int_number": "42",
                "int_or_null": "null",
                "float_number": "14.91",
                "bouillon": "affirmative",
                "string_uuid": "52c76d2c-514f-49ba-b8f7-09065b214e95",
            }
        ),
        (
            {
                "int_number": "14.91",
                "int_or_null": "null",
                "float_number": "14.91",
                "bouillon": "false",
                "string_uuid": "52c76d2c-514f-49ba-b8f7-09065b214e95",
            }
        ),
        (
            {
                "int_number": "1491",
                "int_or_null": "null",
                "float_number": "14.91",
                "bouillon": "false",
                "string_date": "There's a tear in the Space Time Continuum!",
            }
        ),
    ],
    ids=["invalid_uuid", "invalid_bool", "invalid_int", "invalid_date"],
)
def test_from_uncast_dict_validation_fails(instance):
    with pytest.raises(ValidationError) as exc:
        TypecastingEvent.from_uncast_dict(instance)
    assert "Failed validating" in str(exc.value)


def test_subclassing_root_schema():
    with pytest.raises(ValueError) as excinfo:

        class TestSubClassFromEvent(Event):
            table = "dummy_mapping"

    assert "did not declare a JSON schema." in str(excinfo.value)


def test_subclassing_with_schema_mismatch():
    with pytest.raises(EventDefinitionError):

        class TestSubClassFromEvent(Event):
            schema = "dummy-event.json"
            table = "dummy_mapping"


def test_subclassing_different_schema_invalid_data():
    with pytest.raises(ValidationError):
        SimpleEvent(**{"data": "more_data missing here"})


def test_subclassing_missing_schema():
    with pytest.raises(ValueError) as excinfo:

        class TestSubClassFromEvent(Event):
            schema = "nonexistent-schema.json"
            table = "dummy_mapping"

    assert "Cannot resolve schema path" in str(excinfo.value)


def test_subclassing_missing_table():
    with pytest.raises(ValueError) as excinfo:

        class TestSubClassMissingTable(Event):
            schema = "dummy-event.json"

    assert "did not declare a database table mapping." in str(excinfo.value)
