-- migrate:up
CREATE TABLE dummy_events (
  uuid uuid NOT NULL,
  event_time timestamptz NOT NULL,
  schema_title varchar NOT NULL,
  schema_version varchar NOT NULL,
  reader varchar NOT NULL,
  target varchar NOT NULL,
  integer_value smallint NOT NULL,
  float_value numeric NOT NULL,
  CONSTRAINT pk_dummy_event PRIMARY KEY (event_time, uuid)
);

-- migrate:down
DROP TABLE dummy_events;
