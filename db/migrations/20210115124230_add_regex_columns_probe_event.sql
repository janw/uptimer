-- migrate:up
ALTER TABLE probe_events ADD COLUMN regex varchar;
ALTER TABLE probe_events ADD COLUMN matches_regex boolean;

-- migrate:down
ALTER TABLE probe_events DROP COLUMN regex;
ALTER TABLE probe_events DROP COLUMN matches_regex;
