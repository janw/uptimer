import json

from structlog import get_logger

from uptimer import events

logger = get_logger()


def loads(body):
    data = json.loads(body)
    classname = data.get("schema_title")

    if not classname:
        raise ValueError("Body must contain 'schema_title' key")

    logger.debug(
        f"Trying to create a {classname} instance from request: {body}",
        classname=classname,
    )
    return getattr(events, classname).from_json(data)


def dumps(event):
    return event.to_json().encode("ascii")
