from jsonschema.exceptions import ValidationError
from psycopg2 import sql
from psycopg2.errors import DataError, IntegrityError
from psycopg2.extras import execute_batch

from uptimer.events import Event
from uptimer.helpers.postgres import get_postgres_conn
from uptimer.helpers.threads import ProcessingThread
from uptimer.plugins.writers import WriterPlugin


class Plugin(WriterPlugin):
    plugin_type = "postgres event writer"
    event_type = Event
    required_settings = ("database_url",)
    optional_settings = (
        "postgres_pagesize",
        "postgres_queue_timeout",
    )

    def __init__(self, *args, **kwargs):
        super().__init__()

        self.postgres_conn = get_postgres_conn(self.settings.database_url)
        self.page_size = self.settings.postgres_pagesize or 5000
        self.timeout = (
            float(self.settings.postgres_queue_timeout)
            if self.settings.postgres_queue_timeout
            else 2.0
        )

    def write(self, payload):

        with self.postgres_conn:
            with ProcessingThread(
                self.write_callback,
                page_size=self.page_size,
                timeout=self.timeout,
                connection=self.postgres_conn,
            ) as processor:
                for event in payload:
                    try:
                        event.validate()
                    except ValidationError:
                        self.logger.exception("Error validating event", exc_info=True)
                        continue

                    processor.put(event, queue_name=event.__class__)

    def write_callback(self, payload, *, connection):
        if not isinstance(payload, list) or len(payload) == 0:
            raise ValueError("Got unexpected payload")

        cursor = connection.cursor()
        first_event = payload[0]
        table = first_event.__class__.table
        keys = first_event.__class__.properties

        query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table),
            sql.SQL(", ").join(map(sql.Identifier, keys)),
            sql.SQL(", ").join(sql.Placeholder() * len(keys)),
        )

        self.logger.debug(f"DB insert query: {query}", query=query)

        values = tuple(
            Plugin.validate_event_type(
                event, strict=False, to_tuple_by_keys=keys, ignore_missing_keys=True
            )
            for event in payload
        )

        logging_properties = {
            "event_count": len(payload),
            "event_type": first_event.__class__.__name__,
            "table": table,
        }
        self.logger.info(
            f"Writing {len(payload)} {first_event.__class__.__name__}s "
            f"to table {table}.",
            **logging_properties,
        )

        try:
            execute_batch(cursor, query, values, page_size=self.page_size)
            connection.commit()
        except IntegrityError as exc:  # UniqueViolation is a subclass of IntegrityError
            self.logger.warning(
                "Caught integrity violation.", **logging_properties, exc_info=exc
            )
            connection.commit()
            self.try_single_inserts(connection, cursor, query, values)
        except DataError:
            self.logger.exception("Caught database error.", **logging_properties)
            connection.commit()
        except Exception:
            self.logger.exception(
                "Caught unhandled exception. Reraising.", **logging_properties
            )
            raise
        cursor.close()

    def try_single_inserts(self, connection, cursor, query, values):
        self.logger.info("Trying insert with single rows")

        for row in values:
            try:
                cursor.execute(query, vars=row)
            except IntegrityError as exc:
                self.logger.warning(
                    f"Found offending row: {row}", row=row, exc_info=exc
                )
            finally:
                connection.commit()
