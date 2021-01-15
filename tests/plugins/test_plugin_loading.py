import pytest

from uptimer.plugins import load_plugin, resolve_entrypoint
from uptimer.plugins.readers.dummies.dummy_events import Plugin as DummyEventPlugin
from uptimer.plugins.readers.probes.http import HTTPProbe


@pytest.mark.parametrize(
    "entrypoint,expected",
    [
        (
            "uptimer.plugins.readers.probes.http:HTTPProbe",
            ("uptimer.plugins.readers.probes.http", "HTTPProbe"),
        ),
        (
            "uptimer.plugins.readers.probes.http",
            ("uptimer.plugins.readers.probes.http", "Plugin"),
        ),
        ("doesnt.care.about.this", ("doesnt.care.about.this", "Plugin")),
    ],
    ids=["colon_separated", "without_classname", "nonexistent_module"],
)
def test_resolve_entrypoint(entrypoint, expected):
    returned = resolve_entrypoint(entrypoint)

    assert returned == expected


def test_resolve_entrypoint_invalid():
    entrypoint = "some.entry.point.with:TooMany:Colons"

    with pytest.raises(ValueError):
        resolve_entrypoint(entrypoint)


@pytest.mark.parametrize(
    "entrypoint,expected",
    [
        ("uptimer.plugins.readers.probes.http", HTTPProbe),
        (
            {"entrypoint": "uptimer.plugins.readers.probes.http"},
            HTTPProbe,
        ),
        (
            {
                "entrypoint": "uptimer.plugins.readers.probes.http",
                "payload": "Aw yiss. Cat Facts.",
            },
            HTTPProbe,
        ),
        ("readers.probes.http", HTTPProbe),
        (HTTPProbe, HTTPProbe),
    ],
    ids=["str", "dict", "dict_with_payload", "shortened_syntax", "plugin_class"],
)
def test_load_plugin_from_entrypoint(entrypoint, expected):
    plugin = load_plugin(entrypoint)

    assert isinstance(plugin, expected)


@pytest.mark.parametrize(
    "entrypoint,error",
    [
        (
            "uptimer.plugins.readers.probes.http:NonexistentPlugin",
            AttributeError,
        ),
        ("some.nonexistent.entry.point:AnotherOneNotFound", ModuleNotFoundError),
        ({"payload": "Exists"}, ValueError),
        (42, ValueError),
    ],
    ids=[
        "nonexistent_class",
        "nonexistent_module",
        "dict_missing_entrypoint_key",
        "wrong_type",
    ],
)
def test_load_plugin_from_invalid_entrypoint(entrypoint, error):

    with pytest.raises(error):
        load_plugin(entrypoint)


@pytest.mark.parametrize(
    "entrypoint, parameters, event_assertion",
    [
        (
            "uptimer.plugins.readers.dummies.dummy_events_with_parameters",
            {"supplied_parameter": "i_am_a_parameter"},
            lambda e: e[0]["target"] == "i_am_a_parameter",
        ),
        (DummyEventPlugin, {"dummy_event_count": 25}, lambda e: len(e) == 25),
    ],
    ids=["entrypoint_string", "plugin_class"],
)
def test_load_plugin_with_parameters(entrypoint, parameters, event_assertion):
    plugin = load_plugin(entrypoint, parameters=parameters)

    events = list(plugin.read())
    assert event_assertion(events)
