"""Exceptions raised by the Moodle Web Services integration layer."""

from __future__ import annotations


class MoodleError(Exception):
    """Base class for all Moodle integration errors."""


class MoodleNotConfiguredError(MoodleError):
    """Raised when Moodle settings are missing (base URL / token)."""

    def __init__(self) -> None:
        super().__init__(
            "Moodle is not configured. Set MOODLE_BASE_URL and MOODLE_WSTOKEN."
        )


class MoodleConnectionError(MoodleError):
    """Raised when Moodle cannot be reached or times out."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class MoodleAPIError(MoodleError):
    """Raised when Moodle returns a Web Service error or an unexpected response."""

    def __init__(self, errorcode: str, message: str) -> None:
        super().__init__(message)
        self.errorcode = errorcode
        self.message = message