import pytest

from uptimer.core import settings as dynaconf_settings
from uptimer.plugins.settings import PluginSettings


@pytest.mark.parametrize(
    "setting_names", [(("lists_work", "yes_they_do"))], ids=["tuple"]
)
def test_valid_settings_names(setting_names):
    assert PluginSettings._validate_settings_names(setting_names) == list(setting_names)
    assert PluginSettings(required=(), optional=setting_names, sources=()) is not None


@pytest.mark.parametrize(
    "setting_names",
    [
        (["test_setting_tuples_are_bad", "another_setting"]),
        ({"and_so_are_sets", "cool"}),
    ],
    ids=["tuple", "set"],
)
def test_invalid_settings_iterables(setting_names):
    with pytest.raises(ValueError):
        PluginSettings(required=(), optional=setting_names, sources=())


@pytest.mark.parametrize(
    "setting_names",
    [
        (("1nv4lid_first_character", "another_setting")),
        (("metal-dash", "super_bad")),
        (("you_get_a_car", "you_get_a_car", "everybody_gets_a_car")),
        (("THIS_IS_AN_IMPORTANT_SETTING", "BETTER_USE_ALL_CAPS")),
    ],
    ids=["invalid_char0", "invalid_char1", "duplicate_names", "no_caps_allowed"],
)
def test_invalid_settings_names(setting_names):
    with pytest.raises(ValueError):
        PluginSettings._validate_settings_names(setting_names)


COMMON_SOURCE = {
    "this_setting": 1337,
    "another_thing": True,
    "really_unsettling": "myvalue",
}


@pytest.mark.parametrize(
    "sources, required, optional, expected",
    [
        ((COMMON_SOURCE,), (), ("this_setting",), {"this_setting": 1337}),
        ((COMMON_SOURCE,), (), iter(("this_setting",)), {"this_setting": 1337}),
        (
            (COMMON_SOURCE,),
            ("this_setting",),
            ("this_can_be_missing",),
            {"this_setting": 1337, "this_can_be_missing": None},
        ),
        (
            (COMMON_SOURCE, {"this_setting": 42}),
            (),
            ("this_setting",),
            {"this_setting": 42},
        ),
        (
            (COMMON_SOURCE, {"secondary_setting": 42}),
            ("secondary_setting",),
            ("this_setting",),
            {"this_setting": 1337, "secondary_setting": 42},
        ),
        (
            ({"secondary_setting": 42}, COMMON_SOURCE),
            ("secondary_setting",),
            ("this_setting",),
            {"this_setting": 1337, "secondary_setting": 42},
        ),
    ],
    ids=[
        "default",
        "settings_in_iterator",
        "missing_optional",
        "next_source_overrides_value",
        "sources_merged",
        "sources_merged_inverse order",
    ],
)
def test_parsing_settings(sources, required, optional, expected):
    parsed = PluginSettings._parse_settings(required, optional, sources)
    assert parsed == expected


@pytest.mark.parametrize(
    "sources, required, optional",
    [((COMMON_SOURCE,), ("this_setting_is_required",), ("this_can_be_missing",))],
    ids=["missing_required"],
)
def test_parsing_settings_missing_required(sources, required, optional):
    with pytest.raises(ValueError):
        PluginSettings._parse_settings(required, optional, sources)


def test_object_instantiation():

    psettings = PluginSettings(required=(), optional=(), sources=(COMMON_SOURCE,))
    for key in COMMON_SOURCE.keys():
        assert key not in psettings

    psettings = PluginSettings(
        required=(),
        optional=("this_setting", "really_unsettling"),
        sources=(COMMON_SOURCE,),
    )
    assert psettings.this_setting == psettings["this_setting"] == 1337
    assert psettings.really_unsettling == psettings["really_unsettling"] == "myvalue"

    psettings.this_setting = 42
    assert psettings.this_setting == psettings["this_setting"] == 42

    psettings["this_setting"] = 7475
    assert psettings.this_setting == psettings["this_setting"] == 7475

    with pytest.raises(AttributeError):
        psettings.nonexistent_setting

    with pytest.raises(KeyError):
        psettings["nonexistent_setting"]

    assert psettings.get("nonexistent_setting") is None

    psettings["nonexistent_setting"] = "make it exist"
    assert (
        psettings.nonexistent_setting
        == psettings["nonexistent_setting"]
        == "make it exist"
    )


def test_object_instantiation_missing_required():
    with pytest.raises(ValueError):
        PluginSettings(
            required=("missing",),
            optional=("this_setting", "really_unsettling"),
            sources=(COMMON_SOURCE),
        )


def test_object_instantiation_with_dynaconf():
    PluginSettings(
        required=("database_url",),
        optional=("this_setting", "really_unsettling"),
        sources=(dynaconf_settings, COMMON_SOURCE),
    )
