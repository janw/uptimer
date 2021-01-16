import json
from datetime import datetime
from uuid import UUID

import pytest

from uptimer.events.formats import JSONEncoder, is_uuid


@pytest.mark.parametrize(
    "data_input,expected_output",
    [
        (datetime(2021, 1, 5, 12, 34), '"2021-01-05T12:34:00+00:00"'),
        (
            UUID("52c76d2c-514f-49ba-b8f7-09065b214e99"),
            '"52c76d2c-514f-49ba-b8f7-09065b214e99"',
        ),
        ("regular string", '"regular string"'),
        (123, "123"),
        (dict(this=42), '{"this": 42}'),
    ],
    ids=["datetime", "uuid", "string", "integer", "dict"],
)
def test_jsonencoder_types(data_input, expected_output):
    dumped = json.dumps(data_input, cls=JSONEncoder)
    assert dumped == expected_output


@pytest.mark.parametrize(
    "data_input,expected_output",
    [
        (datetime(2021, 1, 5, 12, 34), False),
        (UUID("52c76d2c-514f-49ba-b8f7-09065b214e99"), False),  # Must be of type string
        ("some string", False),
        ("52c76d2x-514f-49ba-b8f7-09065b214eyy", False),  # Contains invalid chars
        ("52c76d2c-514f-49ba-b8f7-09065b214e99", True),
    ],
    # ids=["datetime", "uuid", "re_pattern", "string", "integer", "dict"],
)
def test_format_checker_is_uuid(data_input, expected_output):
    assert is_uuid(data_input) == expected_output
