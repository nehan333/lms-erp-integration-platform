"""Moodle Web Services integration package.

Clean integration layer for the Moodle LMS (Sprint 7). It exposes:
- ``MoodleClient`` — authenticated REST client with timeouts and response validation
- payload builders — ERP model -> Moodle Web Service request params
- ``MoodleSyncService`` — orchestration that records outcomes in ``sync_logs``
"""

from app.integrations.moodle.client import MoodleClient
from app.integrations.moodle.errors import (
    MoodleAPIError,
    MoodleConnectionError,
    MoodleError,
    MoodleNotConfiguredError,
)

__all__ = [
    "MoodleClient",
    "MoodleAPIError",
    "MoodleConnectionError",
    "MoodleError",
    "MoodleNotConfiguredError",
]