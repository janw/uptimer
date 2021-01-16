import re
import time
from collections import namedtuple
from os import path
from pathlib import Path
from typing import Any, Union
from urllib.parse import urlparse

import yaml
from requests import RequestException, Session

from uptimer import events
from uptimer.plugins.mixins import DistributeWorkMixin
from uptimer.plugins.readers import ReaderPlugin

DEFAULT_TLS_VERIFY = True


session = Session()


ProbeTarget = namedtuple("ProbeTarget", "protocol, hostname, port, path")


class HTTPProbe(DistributeWorkMixin, ReaderPlugin):
    plugin_type = "HTTP(S) prober"
    event_type = events.ProbeEvent
    required_settings = ("probe_urls",)
    optional_settings = (
        "probe_regexes",
        "probe_timeout",
        "probe_tls_verify",
        "probe_interval",
    )
    _shutdown = False
    targets = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        session.verify = self._parse_tls_verify(self.settings.probe_tls_verify)

        self.probe_interval = (
            int(self.settings.probe_interval) if self.settings.probe_interval else 30
        )
        self.probe_timeout = (
            int(self.settings.probe_timeout) if self.settings.probe_timeout else 10
        )

        # Parse PROBE_URLS and PROBE_REGEXES from settings, ensure they are of equal
        # length (either by using a single regex for all URLs or one for each, or none
        # at all).
        probe_urls = self._parse_probe_param(self.settings.probe_urls)
        regexes = self._parse_probe_regexes(
            self.settings.probe_regexes, expected_count=len(probe_urls)
        )

        self.targets = self._compile_target_list(regexes, probe_urls)

    def _compile_target_list(self, regexes, probe_urls):
        targets = []
        for regex, url in self.distribute_data(zip(regexes, probe_urls)):
            if not url or not isinstance(url, str):
                raise TypeError(f"URLs must be of type str, not {type(url)}: {url}")
            url = url.strip()
            if not url.startswith("http://") and not url.startswith("https://"):
                raise ValueError("URLs must start with http(s)://")

            url_parts = urlparse(url)

            if url_parts.port is not None:
                port = url_parts.port
            elif url_parts.scheme == "https":
                port = 443
            else:
                port = 80

            targets.append(
                (
                    url,
                    # Keep all static properties in ProbeTarget namedtuple so they can
                    # be forwarded into the event via call to `._as_dict`.
                    ProbeTarget(
                        url_parts.scheme,
                        # Make sure to only include the hostname,
                        # not basic-auth params if present.
                        url_parts.hostname,
                        port,
                        url_parts.path,
                    ),
                    regex,
                )
            )
        return targets

    @staticmethod
    def _parse_tls_verify(tls_verify: Any) -> Union[bool, Path]:
        if tls_verify is None:
            return DEFAULT_TLS_VERIFY
        elif isinstance(tls_verify, bool):
            return tls_verify
        elif isinstance(tls_verify, int):
            tls_verify = str(tls_verify)

        if isinstance(tls_verify, str):
            if tls_verify.lower() in ("n", "no", "false", "0"):
                return False
            elif tls_verify.lower() in ("y", "yes", "true", "1"):
                return True
            elif path.exists(tls_verify):
                return Path(tls_verify)

        raise ValueError(f"Unexpected value for PROBE_TLS_VERIFY: {tls_verify}")

    @staticmethod
    def _parse_probe_param(param):
        if isinstance(param, list):
            return param
        elif isinstance(param, str):
            try:
                loaded = yaml.safe_load(param)

                if isinstance(loaded, str):
                    loaded = [loaded]
                return loaded

            except yaml.YAMLError:
                pass
        raise ValueError(
            "Parameters must be either TOML or YAML parseable or a simple string"
        )

    def _parse_probe_regexes(self, regexes, expected_count=1):
        if not regexes:
            return [None for _ in range(expected_count)]

        regexes = self._parse_probe_param(self.settings.probe_regexes)
        if len(regexes) == 1:
            common_regex = re.compile(regexes[0])
            return [common_regex for _ in range(expected_count)]
        elif len(regexes) == expected_count:
            re.compile(regexes[0])
            return [re.compile(r) for r in regexes]
        else:
            raise ValueError(
                "Number of PROBE_REGEXES must match number of PROBE_URLS or be 1"
            )

    def read(self):

        while True:
            yield from self._probe_all()

            if self._shutdown is True or self.probe_interval < 0:
                self.logger.debug("Shutting down loop.")
                break

            time.sleep(self.probe_interval)

    def _probe_all(self):

        for url, target, regex in self.targets:
            self.logger.info(f"Probing {target.hostname}")

            error = ""
            response = None
            matches_regex = True
            start_time = time.time()
            try:
                response = session.get(url, timeout=self.probe_timeout)
                status_code = response.status_code
            except RequestException as exc:
                error = str(exc)
                status_code = 0

            response_time_ms = round(1000 * (time.time() - start_time))

            if regex and response:
                matches_regex = regex.search(response.text) is not None
                self.logger.info(f"Matches regex /{regex.pattern}/: {matches_regex}")

            yield self.event_type(
                **target._asdict(),
                status_code=status_code,
                response_time_ms=response_time_ms,
                error=error,
                matches_regex=matches_regex,
                regex=regex.pattern if regex else "",
            )

            self.logger.info(f"Done after {response_time_ms} ms")

    def stop(self):
        self._shutdown = True


# Allow generic access via readers.probes.http
Plugin = HTTPProbe
