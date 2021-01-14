from unittest.mock import call

from psycopg2 import sql

from uptimer.events import DummyEvent
from uptimer.plugins.writers import postgres


def test_write_to_postgres(mocker, mockpg):
    event1 = DummyEvent(
        target="target-1", reader="ninjas", integer_value=12345, float_value=123.45
    )

    event2 = DummyEvent(
        target="target-2", reader="pirates", integer_value=54321, float_value=543.21
    )

    execute_batch = mocker.patch(
        "uptimer.plugins.writers.postgres.execute_batch"
    )
    processor = mocker.patch(
        "uptimer.plugins.writers.postgres.ProcessingThread"
    )
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

    execute_batch = mocker.patch(
        "uptimer.plugins.writers.postgres.execute_batch"
    )
    processor = mocker.patch(
        "uptimer.plugins.writers.postgres.ProcessingThread"
    )
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
