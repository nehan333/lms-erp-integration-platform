"""Sprint 7 — Moodle API tests (status + sync endpoints)."""

from __future__ import annotations

from app.api import moodle as moodle_api
from app.services.moodle import MoodleSyncService
from tests.test_moodle_service import FakeMoodleClient, _seed_erp, _success_client


def _override_client(app, client):
    app.dependency_overrides[moodle_api.get_moodle_client] = lambda: client


def test_status_not_configured(client):
    fake = FakeMoodleClient(is_configured=False)
    _override_client(client.app, fake)

    response = client.get("/integrations/moodle/status")

    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is False
    assert "not configured" in (body["message"] or "").lower()

def test_status_connected(client):
    fake = FakeMoodleClient()
    fake.response_overrides["core_webservice_get_site_info"] = {
        "sitename": "Test LMS", "version": "2024042200",
    }
    _override_client(client.app, fake)
    response = client.get("/integrations/moodle/status")
    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is True
    assert body["site_name"] == "Test LMS"
    assert body["moodle_version"] == "2024042200"


def test_status_connection_error(client):
    fake = FakeMoodleClient()
    from app.integrations.moodle.errors import MoodleConnectionError

    fake.error_overrides["core_webservice_get_site_info"] = [
        MoodleConnectionError("boom")
    ]
    _override_client(client.app, fake)
    response = client.get("/integrations/moodle/status")
    assert response.status_code == 200
    assert response.json()["connected"] is False


def test_sync_returns_503_when_not_configured(client, db_session):
    fake = FakeMoodleClient(is_configured=False)
    _override_client(client.app, fake)
    response = client.post("/integrations/moodle/sync")
    assert response.status_code == 503


def test_sync_success_summary(client, db_session):
    _seed_erp(db_session)
    fake = _success_client()
    _override_client(client.app, fake)
    response = client.post("/integrations/moodle/sync")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 5
    assert body["success"] == 5
    assert body["failed"] == 0
    assert len(body["logs"]) == 5
    assert body["logs"][0]["module"] == "moodle"


def test_sync_failed_summary(client, db_session):
    _seed_erp(db_session)
    fake = _success_client()
    from app.integrations.moodle.errors import MoodleAPIError

    fake.response_overrides["core_user_get_users_by_field"] = []
    fake.error_overrides["core_user_create_users"] = [
        MoodleAPIError("invalidparameter", "bad email")
    ]
    _override_client(client.app, fake)
    response = client.post("/integrations/moodle/sync")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 5
    assert body["failed"] >= 1
    assert any(log["action"] == "sync_students" and log["status"] == "Failed" for log in body["logs"])


def test_sync_persists_logs_to_db(client, db_session):
    _seed_erp(db_session)
    fake = _success_client()
    _override_client(client.app, fake)
    response = client.post("/integrations/moodle/sync")
    assert response.status_code == 200
    list_response = client.get("/sync-logs", params={"module": "moodle"})
    assert list_response.json()["total"] == 5


def test_openapi_documents_moodle(client):
    schema = client.get("/openapi.json").json()
    assert "/integrations/moodle/status" in schema["paths"]
    assert "/integrations/moodle/sync" in schema["paths"]
    for name in ["MoodleStatus", "MoodleSyncResult"]:
        assert name in schema["components"]["schemas"]


def test_sync_returns_409_when_already_running(client, db_session, test_engine):
    from sqlalchemy import text

    from app.services.moodle import SYNC_LOCK_KEY

    _seed_erp(db_session)
    fake = _success_client()
    _override_client(client.app, fake)

    conn = test_engine.connect()
    conn.execute(
        text("SELECT pg_try_advisory_lock(:ns, :channel)"),
        {"ns": SYNC_LOCK_KEY[0], "channel": SYNC_LOCK_KEY[1]},
    )
    try:
        response = client.post("/integrations/moodle/sync")
        assert response.status_code == 409
        assert "already running" in response.json()["detail"].lower()
        assert fake.calls == [], "must not touch Moodle while locked"
    finally:
        conn.execute(
            text("SELECT pg_advisory_unlock(:ns, :channel)"),
            {"ns": SYNC_LOCK_KEY[0], "channel": SYNC_LOCK_KEY[1]},
        )
        conn.close()
