def cli():  # pragma: no cover

    from uptimer.core.logging import setup_logging

    setup_logging()

    from uptimer.main import main  # noqa: E402

    main()
