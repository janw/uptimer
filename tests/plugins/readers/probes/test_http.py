from pathlib import Path

import pytest

from uptimer.plugins.readers.probes import http


@pytest.mark.parametrize(
    "input_val, output_val",
    [
        (None, True),
        (True, True),
        (False, False),
        ("yes", True),
        ("no", False),
        (1, True),
        (0, False),
        (__file__, Path(__file__)),
    ],
)
def test_parse_tls_verify(input_val, output_val):
    assert http.HTTPProbe._parse_tls_verify(input_val) == output_val


@pytest.mark.parametrize(
    "input_val, expected",
    [
        ("nope", ValueError),
        ("naha", ValueError),
        ("aye", ValueError),
        (2, ValueError),
        (-1, ValueError),
        ("/nonexistent/path", ValueError),
    ],
)
def test_parse_tls_verify_with_errors(input_val, expected):
    with pytest.raises(expected):
        http.HTTPProbe._parse_tls_verify(input_val)
