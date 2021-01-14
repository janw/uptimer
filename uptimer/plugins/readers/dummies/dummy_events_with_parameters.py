import random

from uptimer.events import DummyEvent
from uptimer.plugins.readers import ReaderPlugin


class Plugin(ReaderPlugin):
    plugin_type = "Generator for DummyEvents"
    event_type = DummyEvent

    optional_settings = ("supplied_parameter",)

    def read(self):
        characters = [
            "mario",
            "luigi",
            "peach",
            "toad",
            "yoshi",
            "bowser",
            "daisy",
            "wario",
        ]

        yield DummyEvent(
            target=self.settings.supplied_parameter or "no_parameter_supplied",
            reader=random.choice(characters),
            integer_value=random.randint(0, 1_000_000),
            float_value=random.uniform(0, 1_000_000),
        )

    # Plugin is always generating dummy data; use .read for .dummy_read
    dummy_read = read
