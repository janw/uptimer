-- migrate:up
CREATE DOMAIN ip_port AS integer
   CHECK(VALUE > 0 AND VALUE < 65536);


-- migrate:down
DROP DOMAIN ip_port;
