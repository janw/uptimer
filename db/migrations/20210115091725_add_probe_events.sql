-- migrate:up
CREATE TABLE probe_events (
    uuid uuid NOT NULL,
    event_time timestamptz NOT NULL,
    schema_title varchar NOT NULL,
    schema_version varchar NOT NULL,
    protocol varchar,
    hostname varchar NOT NULL,
    port ip_port NOT NULL,
    path varchar,
    status_code integer NOT NULL,
    response_time_ms integer NOT NULL,
    error varchar,
    CONSTRAINT pk_probe_events PRIMARY KEY (uuid, event_time)
);

CREATE INDEX idx_probe_events ON probe_events USING btree (hostname, event_time DESC NULLS LAST);

-- migrate:down
DROP TABLE probe_events;
