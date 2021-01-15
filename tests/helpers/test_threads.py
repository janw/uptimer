import logging
from queue import Empty, Queue
from unittest.mock import call

import pytest

from uptimer.helpers.threads import ProcessingThread
from uptimer.plugins import ShutdownMarker


def test_processing_thread_init(mocker):
    mock_callback = mocker.MagicMock()
    processor = ProcessingThread(mock_callback)

    assert processor.callback is mock_callback
    assert processor.page_size == 100
    assert processor.block is True
    assert processor.timeout == 5.0

    processor._stop_event = mocker.MagicMock(name="stop_event")
    processor._data["main"] = mocker.MagicMock(name="data")
    processor.is_alive = mocker.MagicMock(name="is_alive", return_value=True)
    processor.join = mocker.MagicMock(name="join")

    processor.put("Testing")
    processor._data["main"].put.assert_called_once_with("Testing")

    processor.stop()
    assert processor.block is False
    processor._stop_event.set.assert_called_once()
    processor._stop_event.is_set.return_value = True

    assert processor.stopped is True
    processor._stop_event.is_set.assert_called_once()


def test_processing_thread_create_queues(mocker):
    mock_callback = mocker.MagicMock()
    processor = ProcessingThread(mock_callback)

    processor.put("Testing")
    processor.put("Testing", queue_name="other queue")
    assert len(processor._data) == 2
    for _, elem in processor._data.items():
        assert isinstance(elem, Queue)
    for name in ("main", "other queue"):
        assert name in processor._data.keys()


def test_processing_thread_queue_page(mocker):
    expected = ["Some Queue Value", "Another Value"]
    expected_data_args = dict(block=True, timeout=5.0)
    processor = ProcessingThread(mocker.MagicMock(name="callback"), page_size=2)

    processor._data["main"] = mocker.MagicMock(name="data")
    processor._data["main"].get.side_effect = expected

    returns = processor._get_page_from_queue()
    assert returns == expected
    processor._data["main"].assert_has_calls(
        [
            call.get(**expected_data_args),
            call.task_done(),
            call.get(**expected_data_args),
            call.task_done(),
        ]
    )


def test_processing_thread_queue_page_empty(mocker):
    processor = ProcessingThread(mocker.MagicMock(name="callback"), page_size=10)
    processor._data["main"] = mocker.MagicMock(name="data")
    processor._data["main"].get.side_effect = Empty

    assert processor._get_page_from_queue() == []
    processor._data["main"].get.assert_called_once()


def test_processing_thread_no_queue(mocker, caplog):
    processor = ProcessingThread(mocker.MagicMock(name="callback"), page_size=10)

    with caplog.at_level(logging.DEBUG):
        assert processor._get_page_from_queue() == []
    assert "No queues present" in caplog.text


def test_processing_thread_shutdown_marker(mocker, caplog):
    processor = ProcessingThread(mocker.MagicMock(name="callback"), page_size=10)
    processor._data["main"] = mocker.MagicMock(name="data")
    processor._data["main"].get.return_value = ShutdownMarker()

    with caplog.at_level(logging.DEBUG):
        assert processor._get_page_from_queue() == []
    assert len(processor._data) == 0
    assert "Received shutdown marker" in caplog.text


def test_processing_thread_check_liveness(mocker, caplog):
    processor = ProcessingThread(mocker.MagicMock(name="callback"), page_size=10)
    processor.is_alive = mocker.MagicMock()
    processor.is_alive.return_value = False

    with caplog.at_level(logging.ERROR):
        processor._check_liveness()
    assert "thread not alive" in caplog.text

    processor.exception = Exception("Random exception")
    with pytest.raises(Exception):
        processor._check_liveness()


def test_processing_thread_run(mocker, caplog):
    expected_data = ["Some Queue Value", "Another Value"]
    expected_empty_state = [False, True]
    mock_callback = mocker.MagicMock(name="callback")
    processor = ProcessingThread(mock_callback, page_size=1)
    processor._data["main"] = mocker.MagicMock(name="data")
    processor._data["main"].get.side_effect = expected_data
    processor._data["main"].empty.side_effect = expected_empty_state
    processor._stop_event = mocker.MagicMock(name="stop_event")
    processor._stop_event.is_set.return_value = True

    with caplog.at_level(logging.DEBUG):
        processor.run()
    mock_callback.assert_has_calls([call([expected_data[0]]), call([expected_data[1]])])
    assert "Finished processing queue" in caplog.text
    assert "Current page size" in caplog.text

    processor._data["main"].get.side_effect = expected_data
    mock_callback.reset_mock()
    mock_callback.side_effect = Exception("Callback failed")
    with caplog.at_level(logging.ERROR):
        processor.run()
    mock_callback.assert_called_once_with([expected_data[0]])
    assert "unexpected exception" in caplog.text


def test_processing_thread_run_with_callbarg_args(mocker, caplog):
    expected_data = "Some Queue Value"
    mock_callback = mocker.MagicMock(name="callback")
    processor = ProcessingThread(
        mock_callback, page_size=1, some_arg="present", another_arg=False
    )
    processor._data["main"] = mocker.MagicMock(name="data")
    processor._data["main"].get.return_value = expected_data
    processor._data["main"].empty.return_value = True
    processor._stop_event = mocker.MagicMock(name="stop_event")
    processor._stop_event.is_set.return_value = True

    with caplog.at_level(logging.DEBUG):
        processor.run()
    mock_callback.assert_called_once_with(
        [expected_data], some_arg="present", another_arg=False
    )
    assert "Finished processing queue" in caplog.text
    assert "Current page size" in caplog.text
