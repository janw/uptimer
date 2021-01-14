import pytest

from uptimer.events import Event
from uptimer.exceptions import ValidationError


@pytest.mark.parametrize(
    "instance",
    [({"added_property": "this one has no cast mapping"}), ({"another_property": 42})],
    ids=["invalid_str", "invalid_int"],
)
def test_from_json_invalid_properties(instance):
    # Update with a common base of a valid event
    instance.update(
        {
            "uuid": "52c76d2c-514f-49ba-b8f7-09065b214e95",
            "event_time": "2019-04-10T12:43:05.200947+00:00",
            "schema_title": "Base Event",
            "schema_version": "0.1.0",
        }
    )
    with pytest.raises(ValidationError):
        Event.from_json(instance)
