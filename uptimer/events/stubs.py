import time

from uptimer.events import Event

"""
CREATE TABLE dummy_event
                    (event_time timestamptz NOT NULL,
          reader varchar NOT NULL,
          target varchar NOT NULL,
          uuid uuid NOT NULL,
          integer_value bigint NOT NULL,
          float_value numeric NOT NULL,
          schema_title varchar NOT NULL,
          schema_version varchar NOT NULL,
          CONSTRAINT pk_dummy_event PRIMARY KEY (event_time, uuid)
);

SELECT create_hypertable('dummy_event', 'event_time');
"""


class DummyEvent(Event):
    schema = "dummy-event.json"
    table = "dummy_events"


class JobEvent(Event):
    schema = "job-event.json"
    table = "job_events"

    @property
    def is_expired(self):
        ttl = self.get("ttl_seconds", 0)
        if ttl == 0:
            return False

        now = time.time()
        ttl_reached = self["event_time"].timestamp() + ttl < now
        return ttl_reached


class ProbeEvent(Event):
    schema = "probe-event.json"
    table = "probe_events"
