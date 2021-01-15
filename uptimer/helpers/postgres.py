from functools import lru_cache

import psycopg2.extras
from psycopg2 import connect
from psycopg2.extensions import parse_dsn

# Passing UUID type requires it to be with psycopg2 registered
psycopg2.extras.register_uuid()


@lru_cache(maxsize=4)
def get_postgres_conn(database_url):
    """Return reusable postgres connection for the same arguments.

    If no connection exists, it will be created.
    """

    conn_args = parse_dsn(database_url)
    return connect(**conn_args)
