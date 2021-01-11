def to_none(string):
    if string.lower() in ("none", "null"):
        return None
    raise ValueError("Can't cast property")


def to_bool(string):
    if string.lower() == "true":
        return True
    if string.lower() == "false":
        return False
    raise ValueError("Can't cast property")
