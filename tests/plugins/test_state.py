import logging

from uptimer.plugins.state import PluginState


def test_plugin_state_class():
    ps = PluginState()

    assert ps.queue is None
    assert ps.reader is None
    assert ps.writer is None

    assert hasattr(ps, "stop")
    assert hasattr(ps, "register")

    assert str(ps) == "{queue=None, reader=None, writer=None}"
    assert repr(ps) == "<PluginState: {queue=None, reader=None, writer=None}>"

    ps.register(queue="Foo")
    ps.register(reader="Bar")

    assert str(ps) == "{queue=Foo, reader=Bar, writer=None}"


def test_plugin_state_instance(mocker, caplog):

    queue = mocker.MagicMock(name="QueuePlugin")
    writer = mocker.MagicMock(name="WriterPlugin")

    plugin_state = PluginState()
    plugin_state.register(queue=queue, writer=writer)

    with caplog.at_level(logging.DEBUG):
        plugin_state.stop()
    queue.stop.assert_called_once()
    writer.stop.assert_called_once()

    assert f"Triggering shutdown queue: {queue}" in caplog.text
    assert "Done shutting down queue" in caplog.text
    assert "Nothing to shut down for plugin: reader" in caplog.text
