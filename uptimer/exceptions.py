"""Holds all uptimer-specific exception classes.

All locally implemented classes should inherit from the :class:`UptimerException`
base class to allow exception handling to catch all (expected) uptimer exceptions
separately from unexpected errors.
"""


class UptimerException(Exception):
    """uptimer-specific exception class for other exceptions to subclass from."""

    pass


class ImproperlyConfigured(UptimerException):
    """Exception to be raised when uptimer has been improperly configured.

    This may include missing configuration settings, mutually exclusive options, etc.
    """

    pass


class ValidationError(UptimerException):
    """Raised for failed validation of data structures, for example Events."""

    pass


class DatabaseContentsError(UptimerException):
    """Raised when invalid data is returned from the database."""
