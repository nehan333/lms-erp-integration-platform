"""Sprint 6 — Sync Log module tests (repository, service, and API layers)."""

from __future__ import annotations

import uuid

import pytest

from app.models.sync_log import SyncLog
from app.repositories.sync_log import SyncLogRepository
from app.services.sync_log import SyncLogNotFoundError, SyncLogService


def _seed(db_session):
    db_session.add_all(
        [
            SyncLog(module="student", action="create", status="Success", message="created"),
            SyncLog(module="student", action="update", status="Failed", message="timeout"),
            SyncLog(module="course", action="create", status="Success", message=None),
        ]
    )
    db_session.commit()


# --------------------------------------------------------------------------- #
# Repository layer
# --------------------------------------------------------------------------- #


def test_repo_create_and_get(db_session):
    repo = SyncLogRepository(db_session)
    log = repo.create(module="student", action="create", status="Success", message="ok")
    db_session.commit()
    fetched = repo.get(log.id)
    assert fetched is not None
    assert fetched.module == "student"
    assert fetched.status == "Success"


def test_repo_list_pagination_and_filters(db_session):
    _seed(db_session)
    repo = SyncLogRepository(db_session)

    items, total = repo.list(limit=10, offset=0)
    assert total == 3

    items, total = repo.list(limit=2, offset=0)
    assert total == 3
    assert len(items) == 2

    items, total = repo.list(limit=10, offset=0, module="student")
    assert total == 2

    items, total = repo.list(limit=10, offset=0, action="create")
    assert total == 2

    items, total = repo.list(limit=10, offset=0, status="Failed")
    assert total == 1


# --------------------------------------------------------------------------- #
# Service layer
# --------------------------------------------------------------------------- #


def test_service_get_existing_and_missing(db_session):
    _seed(db_session)
    service = SyncLogService(db_session)
    log = service.list_logs(limit=1, offset=0)[0][0]
    assert service.get(log.id).id == log.id
    with pytest.raises(SyncLogNotFoundError):
        service.get(uuid.uuid4())


def test_service_list(db_session):
    _seed(db_session)
    service = SyncLogService(db_session)
    items, total = service.list_logs(limit=10, offset=0)
    assert total == 3


def test_service_record(db_session):
    service = SyncLogService(db_session)
    log = service.record(module="grade", action="sync", status="Success", message="done")
    assert log.id is not None
    assert log.status == "Success"
    assert service.list_logs(limit=10, offset=0)[1] == 1


# --------------------------------------------------------------------------- #
# API layer
# --------------------------------------------------------------------------- #


def test_api_list_sync_logs(client, db_session):
    _seed(db_session)
    response = client.get("/sync-logs")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3


def test_api_list_sync_logs_filters(client, db_session):
    _seed(db_session)
    response = client.get("/sync-logs", params={"status": "Failed"})
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["status"] == "Failed"

    response = client.get("/sync-logs", params={"module": "student"})
    assert response.json()["total"] == 2


def test_api_list_sync_logs_invalid_status(client, db_session):
    response = client.get("/sync-logs", params={"status": "Pending"})
    assert response.status_code == 422


def test_api_get_sync_log(client, db_session):
    _seed(db_session)
    log_id = db_session.query(SyncLog).first().id
    response = client.get(f"/sync-logs/{log_id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(log_id)


def test_api_get_sync_log_not_found(client):
    response = client.get(f"/sync-logs/{uuid.uuid4()}")
    assert response.status_code == 404


def test_openapi_documents_sync_logs(client):
    schema = client.get("/openapi.json").json()
    assert "/sync-logs" in schema["paths"]
    assert "/sync-logs/{sync_log_id}" in schema["paths"]
    for name in ["SyncLogRead", "SyncLogList"]:
        assert name in schema["components"]["schemas"]