from pprint import pprint

from uptimer.events import Event
from uptimer.plugins.writers import WriterPlugin


class Stdout(WriterPlugin):
    event_type = Event
    optional_settings = ("stdout_truncate_settings",)

    def write(self, payload):
        self.logger.info("Outputting payload to stdout")

        truncate = self.settings.stdout_truncate_settings
        for idx, event in enumerate(payload):
            if truncate and idx >= truncate:
                break
            pprint(self.validate_event_type(event, strict=False))

    plugin_type = "Stdout Writer"


Plugin = Stdout
