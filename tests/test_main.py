import logging
import os

import pytest

from uptimer.core import settings
from uptimer.main import main


def test_main_func(mocker, log):
    loader = mocker.patch("uptimer.main.load_plugin")
    processor = mocker.patch("uptimer.main.static_reader_writer_processor")

    main()

    assert len(log.records) > 0
    for record in log.records:
        assert record.name.startswith("uptimer.")
    assert "Starting uptimer" in str(log.records[0].msg)

    loader.assert_called_once_with("writers.stdout")
    processor.assert_called_once_with(loader(), "some.plugin")


def test_main_func_with_queue_plugin(mocker):
    os.environ["TESTING_QUEUE_PLUGIN"] = "my.favorite.queue.plugin"
    settings.reload()

    loader = mocker.patch("uptimer.main.load_plugin")
    processor = mocker.patch("uptimer.main.queue_processor")
    static_processor = mocker.patch("uptimer.main.static_reader_writer_processor")

    main()

    loader.assert_called_once_with("writers.stdout")
    processor.assert_called_once_with(loader(), "my.favorite.queue.plugin")
    static_processor.assert_not_called()
    del os.environ["TESTING_QUEUE_PLUGIN"]


def test_main_with_exception_before_loop(mocker):

    register_handlers = mocker.patch(
        "uptimer.main.register_handlers", side_effect=Exception
    )

    with pytest.raises(Exception):
        main()
    register_handlers.assert_called_once()


def test_main_with_log_level(mocker):
    mocker.patch("uptimer.main.load_plugin")
    mocker.patch("uptimer.main.static_reader_writer_processor")
    mocker.patch("uptimer.main.register_handlers")

    settings.reload()
    main()
    assert logging.root.level == logging.WARNING

    os.environ["TESTING_LOG_LEVEL"] = "debug"
    settings.reload()
    from uptimer.core.logging import setup_logging

    setup_logging()
    assert logging.root.level == logging.DEBUG
    del os.environ["TESTING_LOG_LEVEL"]
