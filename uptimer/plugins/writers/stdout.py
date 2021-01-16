import sys

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
            sys.stdout.write(
                self.validate_event_type(event, strict=False).to_json(
                    indent=2, sort_keys=2
                )
                + "\n"
            )

    plugin_type = "Stdout Writer"


Plugin = Stdout
