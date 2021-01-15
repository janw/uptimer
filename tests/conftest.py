import re
import tempfile
from collections import namedtuple
from glob import glob
from os import chdir
from os import environ
from os import getcwd
from os import path

import pytest

from uptimer.events import SCHEMATA_PATH
from uptimer.helpers.postgres import get_postgres_conn


MARKABLE_FIXTURES = {"postgres_fixture": "postgres", "postgres_conn": "postgres"}


def pytest_collection_modifyitems(config, items):
    """Adds markers to items based on the fixtures named in `MARKABLE FIXTURES`"""
    for item in items:
        for fixture in item.fixturenames:
            if fixture in MARKABLE_FIXTURES:
                item.add_marker(MARKABLE_FIXTURES[fixture])


@pytest.fixture()
def cleandir(request):
    newpath = tempfile.mkdtemp()
    old_cwd = getcwd()
    chdir(newpath)

    def cleanup():
        chdir(old_cwd)

    request.addfinalizer(cleanup)

    return newpath


def pytest_generate_tests(metafunc):
    """Generates parametrized tests on-the-fly through pytest fixtures.

    Currently implements:

        jsonschemafile
            Collect all JSON schema files for Uptimer events. Each schema file will
            become be turned into a single execution on test functions using this
            fixture. Useful in, e.g., validating the schema file syntax.

    Args:
        metafunc: Pytest-provided meta fixture for generating more fixtures.
    """

    if "jsonschemafile" in metafunc.fixturenames:
        schemata = glob(path.join(SCHEMATA_PATH, "*.json"))
        metafunc.parametrize(
            "jsonschemafile", schemata, ids=[path.basename(s) for s in schemata]
        )


@pytest.fixture
def log(caplog):
    from uptimer.core.logging import setup_logging

    setup_logging()
    return caplog


re_split_migration = re.compile(r"^\-\-.*(migrate\:(?:up|down)).*$", re.MULTILINE)


@pytest.fixture(scope="session")
def postgres_conn():
    return get_postgres_conn(
        environ.get(
            "TESTING_DATABASE_URL", "postgres://postgres:password@localhost/test_db"
        ),
    )


@pytest.fixture()
def postgres_fixture(request, postgres_conn):
    base_dir = path.dirname(request.fspath)
    down_migrations = []

    def _load_fixture(sql_file):
        abspath = sql_file
        if not path.isfile(abspath):
            abspath = path.join(base_dir, abspath)
        if not path.isfile(abspath):
            raise FileNotFoundError(f"File not found as {sql_file} or {abspath}")

        # Read and split the fixture into up/down migration by `migrate:` comment
        migrate_up = None
        migrate_down = None
        with open(abspath) as fp:
            fixture = fp.read()
            splits = re_split_migration.split(fixture)
            for idx, line in enumerate(splits):
                if line == "migrate:up":
                    migrate_up = splits[idx + 1].strip()
                elif line == "migrate:down":
                    migrate_down = splits[idx + 1].strip()

        if migrate_up is None or migrate_down is None:
            raise ValueError(
                "Postgres fixture must contain both migrate:up and "
                "migrate:down statements"
            )

        with postgres_conn:
            with postgres_conn.cursor() as cursor:
                cursor.execute(migrate_up)

        down_migrations.append(migrate_down)
        return migrate_up, migrate_down

    yield _load_fixture

    # Everything after `yield` pytest will use as teardown code
    for migration in down_migrations:
        with postgres_conn:
            with postgres_conn.cursor() as cursor:
                cursor.execute(migration)


mock_postgres_tuple = namedtuple(
    "mock_postgres", ["connection", "cursor", "cursor_ctx"]
)


@pytest.fixture()
def mockpg(mocker):
    get_conn = mocker.patch("uptimer.plugins.writers.postgres.get_postgres_conn")
    get_conn.return_values = mocker.MagicMock(name="connection instance")
    get_conn.return_value.cursor = mocker.MagicMock()
    get_conn.return_value.cursor.return_value = mocker.MagicMock()

    return mock_postgres_tuple(
        get_conn.return_value,
        get_conn.return_value.cursor,
        get_conn.return_value.cursor.return_value.__enter__.return_value,
    )
