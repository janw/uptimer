import random

from uptimer.events import DummyEvent
from uptimer.plugins.readers import ReaderPlugin


class Plugin(ReaderPlugin):
    plugin_type = "Generator for DummyEvents"
    event_type = DummyEvent
    optional_settings = ("dummy_event_count",)

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

        event_count = self.settings.dummy_event_count or 10

        for idx in range(event_count):
            yield DummyEvent(
                target=f"somewhere-{idx}",
                reader=random.choice(characters),
                integer_value=random.randint(0, 1000000),
                float_value=random.uniform(0, 1000000),
            )

    # Plugin is always generating dummy data; use .read for .dummy_read
    dummy_read = read
