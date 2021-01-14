from os import path
from unittest.mock import call

from uptimer.events import SCHEMATA_PATH
from uptimer.events.cache import SchemaCache


def test_schemacache_init(mocker):

    mocked_open = mocker.patch.object(SchemaCache, "__missing__")

    schema_cache = SchemaCache()
    assert schema_cache is not None
    mocked_open.assert_not_called()


def test_loading_missing_schema(mocker):

    mocked_open = mocker.patch.object(SchemaCache, "__missing__")
    schema_cache = SchemaCache()

    schema_cache["root.json"]
    mocked_open.assert_called_once_with("root.json")


def test_loading_dependant_of_root_json(mocker):
    mocked_open = mocker.patch("builtins.open", side_effect=open)
    calls = [
        call(path.join(SCHEMATA_PATH, "probe-event.json"), "r"),
        call(path.join(SCHEMATA_PATH, "root.json"), "r"),
    ]

    # Defaults to resolve $refs in the schema, should open two files.
    schema_cache = SchemaCache()
    schema_cache["probe-event.json"]
    mocked_open.assert_called()
    assert mocked_open.call_count == 2
    mocked_open.assert_has_calls(calls)
    mocked_open.reset_mock()

    # Non-resolving cache should only open the asked-for file
    schema_cache_non_resolving = SchemaCache(resolve_refs=False)
    schema_cache_non_resolving["probe-event.json"]
    mocked_open.assert_called_once()
    mocked_open.assert_has_calls([calls[0]])


def test_return_cached_result(mocker):
    mocked_open = mocker.patch("builtins.open", side_effect=open)

    schema_cache = SchemaCache()
    schema_cache["probe-event.json"]
    mocked_open.assert_called()
    assert mocked_open.call_count == 2

    # Request the same schema again; call_count stays the same.
    schema_cache["probe-event.json"]
    assert mocked_open.call_count == 2

    # Resolving should have cached root.json as well; call_count stays the same
    schema_cache["root.json"]
    assert mocked_open.call_count == 2
