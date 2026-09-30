"""Sprint 7 — MoodleClient tests using httpx MockTransport."""

from __future__ import annotations

import httpx
import pytest

from app.integrations.moodle.client import MoodleClient
from app.integrations.moodle.errors import (
    MoodleAPIError,
    MoodleConnectionError,
    MoodleNotConfiguredError,
)

BASE_URL = "https://moodle.example.com"


def _client(handler, *, base_url=BASE_URL, wstoken="secret"):
    return MoodleClient(base_url=base_url, wstoken=wstoken, transport=httpx.MockTransport(handler))


def test_call_success():
    def handler(request):
        assert request.url.path.endswith("/webservice/rest/server.php")
        body = request.content.decode()
        assert "wstoken=secret" in body
        assert "wsfunction=core_webservice_get_site_info" in body
        assert "moodlewsrestformat=json" in body
        return httpx.Response(200, json={"sitename": "Test LMS"})

    client = _client(handler)
    assert client.call("core_webservice_get_site_info", {}) == {"sitename": "Test LMS"}


def test_call_moodle_exception():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "exception": "moodle_exception",
                "errorcode": "invalidtoken",
                "message": "Invalid token",
            },
        )

    with pytest.raises(MoodleAPIError) as excinfo:
        _client(handler).call("core_webservice_get_site_info", {})
    assert excinfo.value.errorcode == "invalidtoken"
    assert "Invalid token" in str(excinfo.value)


def test_call_http_error():
    def handler(request):
        return httpx.Response(503, text="service unavailable")

    with pytest.raises(MoodleAPIError) as excinfo:
        _client(handler).call("core_webservice_get_site_info", {})
    assert excinfo.value.errorcode == "http_503"


def test_call_non_json_response():
    def handler(request):
        return httpx.Response(200, text="<html>not json</html>")

    with pytest.raises(MoodleAPIError) as excinfo:
        _client(handler).call("core_webservice_get_site_info", {})
    assert excinfo.value.errorcode == "invalid_response"


def test_call_timeout():
    def handler(request):
        raise httpx.TimeoutException("timed out", request=request)

    with pytest.raises(MoodleConnectionError):
        _client(handler).call("core_webservice_get_site_info", {})


def test_call_connection_error():
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(MoodleConnectionError):
        _client(handler).call("core_webservice_get_site_info", {})


def test_not_configured():
    client = MoodleClient(base_url="", wstoken="")
    assert client.is_configured is False
    with pytest.raises(MoodleNotConfiguredError):
        client.call("core_webservice_get_site_info", {})