from uptimer.events.base import Event
from uptimer.plugins.writers.stdout import Stdout


def test_stdout(capfd):
    writer = Stdout()
    writer.write(iter([Event(message="Hello stdout!")]))
    out, err = capfd.readouterr()
    assert "message': 'Hello stdout!'" in out
