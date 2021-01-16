import logging

import pytest

from uptimer.main import main


def test_main_func(mocker, log):
    loader = mocker.patch("uptimer.main.load_plugin")
    processor = mocker.patch("uptimer.main.static_reader_writer_processor")

    main()

    assert len(log.events) > 0
    assert log.has("Starting uptimer")

    loader.assert_called_once_with("writers.stdout")
    processor.assert_called_once_with(loader(), "some.plugin")


def test_main_func_with_queue_plugin(mocker, conf_override):
    conf_override("QUEUE_PLUGIN", "my.favorite.queue.plugin")

    loader = mocker.patch("uptimer.main.load_plugin")
    processor = mocker.patch("uptimer.main.queue_processor")
    static_processor = mocker.patch("uptimer.main.static_reader_writer_processor")

    main()

    loader.assert_called_once_with("writers.stdout")
    processor.assert_called_once_with(loader(), "my.favorite.queue.plugin")
    static_processor.assert_not_called()


def test_main_with_exception_before_loop(mocker):

    register_handlers = mocker.patch(
        "uptimer.main.register_handlers", side_effect=Exception
    )

    with pytest.raises(Exception):
        main()
    register_handlers.assert_called_once()


def test_main_with_log_level(mocker, conf_override):
    mocker.patch("uptimer.main.load_plugin")
    mocker.patch("uptimer.main.queue_processor")
    mocker.patch("uptimer.main.static_reader_writer_processor")
    mocker.patch("uptimer.main.register_handlers")

    main()
    assert logging.root.level == logging.WARNING

    conf_override("LOG_LEVEL", "debug")
    from uptimer.core.logging import setup_logging

    setup_logging()
    assert logging.root.level == logging.DEBUG
