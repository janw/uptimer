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


@pytest.mark.parametrize(
    "input_val",
    [
        (["http://example.com"]),
        ('["http://example.com"]'),
        ("\n- http://example.com\n"),
        ("http://example.com"),
    ],
    ids=["native_list", "yaml_list_1", "yaml_list_2", "str"],
)
def test_parse_probe_param(input_val):
    expected = ["http://example.com"]
    assert http.HTTPProbe._parse_probe_param(input_val) == expected


@pytest.mark.parametrize(
    "input_val, expected",
    [
        (47, ValueError),
        ('["incomplete', ValueError),
    ],
    ids=["int", "incomplete_list"],
)
def test_parse_probe_param_with_errors(input_val, expected):
    with pytest.raises(expected):
        http.HTTPProbe._parse_probe_param(input_val)


@pytest.mark.parametrize(
    "input_val, expected",
    [
        (
            "http://example.com",
            http.ProbeTarget("http", "example.com", 80, ""),
        ),
        (
            "http://user:mypass@example.com",
            http.ProbeTarget("http", "example.com", 80, ""),
        ),
        (
            "http://user@example.com:9091",
            http.ProbeTarget("http", "example.com", 9091, ""),
        ),
        (
            "https://user@example.com:9092/path",
            http.ProbeTarget("https", "example.com", 9092, "/path"),
        ),
        (
            "https://example.com/path",
            http.ProbeTarget("https", "example.com", 443, "/path"),
        ),
        (
            "https://example.com",
            http.ProbeTarget("https", "example.com", 443, ""),
        ),
    ],
    ids=[
        "default_http",
        "http_auth",
        "http_custom_port",
        "https_custom_port",
        "https_path",
        "https_default",
    ],
)
def test_compile_target_list(input_val, expected):
    prober = http.HTTPProbe()
    targets = prober._compile_target_list([None], [input_val])

    assert len(targets) == 1
    assert targets[0] == (input_val, expected, None)


@pytest.mark.parametrize(
    "input_val, expected",
    [
        (42, TypeError),
        ("ftp://example.com", ValueError),
        ("git://git@github.com:janw/uptimer.git", ValueError),
    ],
    ids=[
        "wrong-type",
        "ftp",
        "git",
    ],
)
def test_compile_target_list_with_errors(input_val, expected):
    prober = http.HTTPProbe()

    with pytest.raises(expected):
        prober._compile_target_list([None], [input_val])
