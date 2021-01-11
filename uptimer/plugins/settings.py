from collections.abc import MutableMapping
from itertools import chain
from typing import Any, Dict, List, Tuple

from munch import Munch


class PluginSettings(Munch):
    def __init__(
        self,
        *,
        required: Tuple[str, ...],
        optional: Tuple[str, ...],
        sources: Tuple[MutableMapping, ...],
    ):

        if not all((isinstance(v, tuple) for v in (required, optional, sources))):
            raise ValueError("PluginSettings arguments must be tuples.")

        self._validate_settings_names(required, optional)
        parsed_settings = self._parse_settings(required, optional, sources)
        self.update(parsed_settings)
        self._required = required
        self._optional = optional
        self._sources = sources

    @staticmethod
    def _validate_settings_names(*settings_lists: Tuple[str, ...]):
        valid_settings: List[str] = []
        for setting in chain(*settings_lists):
            if not setting.isidentifier():
                raise ValueError(f"Setting name `{setting}` is an invalid identifier")
            if not setting.islower():
                raise ValueError(f"Setting name `{setting}` must be lowercase")
            if setting in valid_settings:
                raise ValueError(f"Setting `{setting}` is already present")
            valid_settings.append(setting)
        return valid_settings

    @staticmethod
    def _parse_settings(required, optional, sources) -> Dict[str, Any]:
        parsed_settings = dict()
        for setting in chain(required, optional):
            value = None
            for source in sources:
                if setting in source:
                    value = source.get(setting)
                elif setting.upper() in source:
                    # NOTE: Special case trying with upper-cased version of the setting
                    # to account for Dynaconf's inconsistent behavior when using
                    # `setting in source`. A discussion about this was opened upstream.
                    # See: https://github.com/rochacbruno/dynaconf/issues/272
                    value = source.get(setting.upper())

            if value is None and setting in required:
                raise ValueError(f"Setting {setting} is required")

            parsed_settings[setting] = value
        return parsed_settings
