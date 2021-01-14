from uptimer.events import DummyEvent
from uptimer.plugins.readers.dummies.dummy_events import Plugin


def test_dummy_events():
    p = Plugin()

    events = list(p.read())
    assert len(events) == 10
    for event in events:
        assert isinstance(event, DummyEvent)


def test_dummy_events_custom_count():
    p = Plugin(dummy_event_count=7)

    events = list(p.read())
    assert len(events) == 7
