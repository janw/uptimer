from time import sleep

from uptimer.core.processors import queue_processor, static_reader_writer_processor
from uptimer.events import Event, JobEvent
from uptimer.plugins import BasePlugin


def fixture_static_yield():
    yield Event()


static_yield = fixture_static_yield()


class FixtureTestReader(BasePlugin):
    is_one_shot_reader = True

    def read(self):
        return static_yield


def test_static_reader_writer(mocker):
    writer = mocker.MagicMock()
    writer.write = mocker.MagicMock()

    static_reader_writer_processor(writer, FixtureTestReader)
    writer.write.assert_called_with(static_yield)


def test_queue_processor(mocker):
    writer = mocker.MagicMock()
    writer.write = mocker.MagicMock()
    job = JobEvent(reader=FixtureTestReader, validate=False)
    expiring_job = JobEvent(reader=FixtureTestReader, ttl_seconds=0.1, validate=False)

    class FixtureTestQueueReader(BasePlugin):
        def read(self):
            return [job]

    class FixtureExpiringTestQueueReader(BasePlugin):
        def read(self):
            return [expiring_job]

    queue_processor(writer, FixtureTestQueueReader)
    sleep(0.2)
    queue_processor(writer, FixtureExpiringTestQueueReader)

    # As the second JobEvent is expiring, this should only be called once
    writer.write.assert_called_once_with(static_yield)
