from os import environ
from unittest.mock import call

import pytest
from psycopg2 import sql

from uptimer.core import settings
from uptimer.events import DummyEvent
from uptimer.helpers.postgres import get_postgres_conn
from uptimer.plugins.writers import postgres

require_postgres = pytest.mark.skipif(
    "TESTING_DATABASE_URL" not in environ, reason="No real TESTING_DATABASE_URL set"
)


def test_write_to_postgres(mocker, mockpg):
    event1 = DummyEvent(
        target="target-1", reader="ninjas", integer_value=12345, float_value=123.45
    )

    event2 = DummyEvent(
        target="target-2", reader="pirates", integer_value=54321, float_value=543.21
    )

    execute_batch = mocker.patch("uptimer.plugins.writers.postgres.execute_batch")
    processor = mocker.patch("uptimer.plugins.writers.postgres.ProcessingThread")
    ctx_processor = mocker.MagicMock(name="contextmanaged_processor")
    processor().__enter__.return_value = ctx_processor

    writer_argument = [event1, event2]
    keys = event1.keys()
    expected_tuples = tuple(tuple(e[k] for k in keys) for e in writer_argument)
    query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        sql.Identifier("dummy_events"),
        sql.SQL(", ").join(map(sql.Identifier, keys)),
        sql.SQL(", ").join(sql.Placeholder() * len(keys)),
    )

    writer = postgres.Plugin()
    writer.write(iter(writer_argument))

    assert processor.call_count == 2  # 1x on __init__, 1x when __enter__'ing
    processor().__enter__.assert_called_once()
    ctx_processor.put.assert_has_calls(
        [
            call(event1, queue_name=event1.__class__),
            call(event2, queue_name=event2.__class__),
        ]
    )

    # Called once per processed event
    assert ctx_processor.put.call_count == 2

    mockpg.cursor.return_value.close.assert_not_called()
    execute_batch.assert_not_called()

    # Check the writer callback that does the actual writing to postgres
    writer.write_callback(writer_argument, connection=mockpg.connection)

    mockpg.connection.cursor.assert_called_once()
    execute_batch.assert_called_once_with(
        mockpg.cursor.return_value, query, expected_tuples, page_size=5000
    )
    mockpg.connection.commit.assert_called_once()

    processor().__exit__.assert_called_once()


def test_invalid_event_write_to_postgres(mocker, mockpg):
    event1 = DummyEvent(
        target="target-1", reader="ninjas", integer_value=12345, float_value=123.45
    )

    event2 = DummyEvent(
        target="target-2", reader="pirates", integer_value=54321, float_value=543.21
    )

    event2["uuid"] = "nope"

    execute_batch = mocker.patch("uptimer.plugins.writers.postgres.execute_batch")
    processor = mocker.patch("uptimer.plugins.writers.postgres.ProcessingThread")
    ctx_processor = mocker.MagicMock(name="contextmanaged_processor")
    processor().__enter__.return_value = ctx_processor

    writer_argument = [event1, event2]
    keys = event1.keys()
    expected_tuples = tuple(tuple(e[k] for k in keys) for e in writer_argument)
    query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        sql.Identifier("dummy_events"),
        sql.SQL(", ").join(map(sql.Identifier, keys)),
        sql.SQL(", ").join(sql.Placeholder() * len(keys)),
    )

    writer = postgres.Plugin()
    writer.write(iter(writer_argument))

    assert processor.call_count == 2  # 1x on __init__, 1x when __enter__'ing
    processor().__enter__.assert_called_once()
    ctx_processor.put.assert_has_calls([call(event1, queue_name=event1.__class__)])

    # Called once per processed event
    assert ctx_processor.put.call_count == 1

    mockpg.cursor.return_value.close.assert_not_called()
    execute_batch.assert_not_called()

    # Check the writer callback that does the actual writing to postgres
    writer.write_callback(writer_argument, connection=mockpg.connection)

    mockpg.connection.cursor.assert_called_once()
    execute_batch.assert_called_once_with(
        mockpg.cursor.return_value, query, expected_tuples, page_size=5000
    )
    mockpg.connection.commit.assert_called_once()

    processor().__exit__.assert_called_once()


@require_postgres
def test_postgres_connection_cached():
    db_url = settings.get("DATABASE_URL")
    conn1 = get_postgres_conn(db_url)
    conn2 = get_postgres_conn(db_url)

    assert conn1 is conn2


@require_postgres
def test_postgres_inserts(postgres_conn):
    verify_query = sql.SQL(
        """
SELECT
*
FROM
{}"""
    ).format(sql.Identifier(DummyEvent.table))

    with postgres_conn.cursor() as cursor:
        cursor.execute(verify_query)
        row_count_before = cursor.rowcount

    event1 = DummyEvent(
        target="target-1", reader="ninjas", integer_value=12345, float_value=123.45
    )

    event2 = DummyEvent(
        target="target-2", reader="pirates", integer_value=4321, float_value=543.21
    )
    writer_argument = [event1, event2]

    writer = postgres.Plugin()
    writer.write(iter(writer_argument))

    with postgres_conn.cursor() as cursor:
        cursor.execute(verify_query)
        assert cursor.rowcount == row_count_before + 2

    # Try writing the same events again leading to exception in background thread
    writer.write(iter(writer_argument))

    with postgres_conn.cursor() as cursor:
        cursor.execute(verify_query)
        assert cursor.rowcount == row_count_before + 2

    event3 = DummyEvent(
        target="target-1", reader="ninjas", integer_value=12345, float_value=123.45
    )

    # Try writing a new one, valid
    writer.write(iter([event3]))
    with postgres_conn.cursor() as cursor:
        cursor.execute(verify_query)
        assert cursor.rowcount == row_count_before + 3

    event4 = DummyEvent(
        target="target-1",
        reader="ninjas",
        integer_value=-32999,  # triggers NumericValueOutOfRange on smallint
        float_value=123.45,
    )

    # Try writing another one, trigger DataError, no rowcount increase
    writer.write(iter([event4]))
    with postgres_conn.cursor() as cursor:
        cursor.execute(verify_query)
        assert cursor.rowcount == row_count_before + 3

    event5 = DummyEvent(
        target="target-1",
        reader="ninjas",
        integer_value=7,
        float_value=123.45,
    )

    # One last try with one existing (skipped) and one new (inserted)
    writer.write(iter([event1, event5]))
    with postgres_conn.cursor() as cursor:
        cursor.execute(verify_query)
        assert cursor.rowcount == row_count_before + 4
