"""HTTP client for the Moodle Web Services REST API.

Encapsulates token authentication, request building, timeouts, and response
validation. Every call maps failures to ``MoodleError`` subclasses so callers
never handle raw ``httpx`` exceptions.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.integrations.moodle.errors import (
    MoodleAPIError,
    MoodleConnectionError,
    MoodleNotConfiguredError,
)

REST_ENDPOINT = "/webservice/rest/server.php"
JSON_FORMAT = "json"


class MoodleClient:
    """Thin wrapper around the Moodle Web Services REST endpoint."""

    def __init__(
        self,
        *,
        base_url: str,
        wstoken: str,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.wstoken = wstoken
        self.timeout = timeout
        self._transport = transport

    @classmethod
    def from_settings(cls) -> "MoodleClient":
        """Build a client from the application settings."""
        return cls(
            base_url=settings.MOODLE_BASE_URL,
            wstoken=settings.MOODLE_WSTOKEN,
            timeout=settings.MOODLE_TIMEOUT_SECONDS,
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.wstoken)

    def _url(self) -> str:
        return f"{self.base_url}{REST_ENDPOINT}"

    def _payload(self, wsfunction: str, params: dict[str, Any]) -> dict[str, Any]:
        return {
            "wstoken": self.wstoken,
            "wsfunction": wsfunction,
            "moodlewsrestformat": JSON_FORMAT,
            **params,
        }

    def call(self, wsfunction: str, params: dict[str, Any]) -> Any:
        """Invoke ``wsfunction`` with ``params`` and return the parsed response."""
        if not self.is_configured:
            raise MoodleNotConfiguredError()

        request_params = self._payload(wsfunction, params)
        try:
            with httpx.Client(timeout=self.timeout, transport=self._transport) as client:
                response = client.post(self._url(), data=request_params)
        except httpx.TimeoutException as exc:
            raise MoodleConnectionError(
                f"Timed out calling Moodle function '{wsfunction}'"
            ) from exc
        except httpx.HTTPError as exc:
            raise MoodleConnectionError(
                f"Connection error calling Moodle function '{wsfunction}': {exc}"
            ) from exc

        if response.status_code >= 400:
            raise MoodleAPIError(
                f"http_{response.status_code}",
                f"Moodle returned HTTP {response.status_code} for '{wsfunction}'",
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise MoodleAPIError(
                "invalid_response",
                f"Moodle returned a non-JSON response for '{wsfunction}'",
            ) from exc

        if isinstance(payload, dict) and "exception" in payload:
            raise MoodleAPIError(
                str(payload.get("errorcode", "unknown")),
                str(payload.get("message", str(payload))),
            )

        return payload