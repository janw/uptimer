from uptimer.plugins import BasePlugin
from uptimer.plugins.settings import PluginSettings


def test_baseplugin_init():

    bp = BasePlugin()

    assert hasattr(bp, "settings")
    assert isinstance(bp.settings, PluginSettings)

    assert repr(bp).startswith("Plugin(")

    # Module string (uptimer.plugins) is removed for posterity on "included" plugins
    assert str(bp) == "BasePlugin"
