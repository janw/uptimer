from functools import lru_cache

import psycopg2.extras
from psycopg2 import connect

# Passing UUID type requires it to be with psycopg2 registered
psycopg2.extras.register_uuid()


@lru_cache(maxsize=4)
def get_postgres_conn(*args, **kwargs):
    """Return reusable postgres connection for the same arguments.

    If no connection exists, it will be created.
    """
    return connect(*args, **kwargs)
