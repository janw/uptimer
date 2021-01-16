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


def test_plugin_state_instance(mocker, log):

    queue = mocker.MagicMock(name="QueuePlugin")
    writer = mocker.MagicMock(name="WriterPlugin")

    plugin_state = PluginState()
    plugin_state.register(queue=queue, writer=writer)

    plugin_state.stop()
    queue.stop.assert_called_once()
    writer.stop.assert_called_once()

    log.has("Triggering shutdown queue: {queue}")
    log.has("Done shutting down queue")
    log.has("Nothing to shut down for plugin: reader")
