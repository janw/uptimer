import yaml
import time
from collections import namedtuple
from urllib.parse import urlparse

from requests import RequestException, Session, Timeout

from uptimer import events
from uptimer.plugins.readers import ReaderPlugin
from uptimer.plugins.mixins import DistributeWorkMixin

session = Session()


ProbeTarget = namedtuple("ProbeTarget", "protocol, hostname, port, path")


class HTTPProbe(DistributeWorkMixin, ReaderPlugin):
    plugin_type = "HTTP(S) prober"
    event_type = events.ProbeEvent
    required_settings = ("probe_urls",)
    optional_settings = ("probe_timeout", "probe_tls_verify", "probe_interval")
    _shutdown = False
    targets = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tls_verify = (
            False
            if self.settings.probe_tls_verify
            and self.settings.probe_tls_verify.lower() in ("n", "no", "false", "0")
            else True
        )
        self.probe_interval = (
            int(self.settings.probe_interval) if self.settings.probe_interval else 30
        )
        self.probe_timeout = (
            int(self.settings.probe_timeout) if self.settings.probe_timeout else 10
        )

        self.targets = []
        probe_urls = self._parse_probe_urls()
        for url in self.distribute_data(probe_urls):
            url = url.strip()
            if not url:
                continue

            url_parts = urlparse(url)

            if url_parts.port is not None:
                port = url_parts.port
            elif url_parts.scheme == "https":
                port = 443
            else:
                port = 80

            self.targets.append(
                (
                    url,
                    ProbeTarget(
                        url_parts.scheme, url_parts.hostname, port, url_parts.path
                    ),
                )
            )

    def _parse_probe_urls(self):
        if isinstance(self.settings.probe_urls, list):
            return self.settings.probe_urls
        try:
            return yaml.safe_load(self.settings.probe_urls)
        except yaml.YAMLError:
            self.logger.warning(
                "Could not YAML-parse PROBE_URLS:", probe_urls=self.settings.probe_urls
            )
            pass

        # Attempt crude parsing from comma-separated URLs
        parsed_urls = [
            u for u in map(str.strip, self.settings.probe_urls.split(",")) if u
        ]
        self.logger.warning(
            "Parsed PROBE_URLS as comma-separated values", parsed_urls=str(parsed_urls)
        )
        return

    def read(self):

        while True:
            yield from self._probe_all()

            if self._shutdown is True or self.probe_interval < 0:
                self.logger.debug("Shutting down loop.")
                break

            time.sleep(self.probe_interval)

    def _probe_all(self):

        for url, target in self.targets:
            self.logger.info(f"Probing {target.hostname}")

            error = ""
            start_time = time.time()
            try:
                response = session.get(
                    url, timeout=self.probe_timeout, verify=self.tls_verify
                )
                status_code = response.status_code
            except Timeout:
                error = "Connection timed out"
                status_code = 0
            except RequestException:
                error = "Exception encountered during probe"
                status_code = 0

            response_time_ms = round(1000 * (time.time() - start_time))

            yield self.event_type(
                **target._asdict(),
                status_code=status_code,
                response_time_ms=response_time_ms,
                error=error,
            )

            self.logger.info(f"Done after {response_time_ms} ms")

    def stop(self):
        self._shutdown = True


# Allow generic access via readers.probes.http
Plugin = HTTPProbe
