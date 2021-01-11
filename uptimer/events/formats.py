import json
import re
from datetime import datetime, timezone
from uuid import UUID as uuid

import jsonschema
from structlog import get_logger

format_checker = jsonschema.FormatChecker()

uuid_re = re.compile(
    r"^[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}$"
)

logger = get_logger()


@format_checker.checks("uuid")
def is_uuid(instance):
    if not isinstance(instance, jsonschema.compat.str_types):
        return True
    return uuid_re.match(instance) is not None


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return self.from_datetime(obj)
        if isinstance(obj, uuid):
            return self.from_uuid(obj)
        return json.JSONEncoder.default(self, obj)

    @staticmethod
    def from_datetime(obj):
        if not obj.tzinfo:
            logger.warning(f"Got naive datetime object {obj}, localizing to UTC")
            obj = obj.replace(tzinfo=timezone.utc)
        return obj.isoformat()

    @staticmethod
    def from_uuid(obj):
        return str(obj)
