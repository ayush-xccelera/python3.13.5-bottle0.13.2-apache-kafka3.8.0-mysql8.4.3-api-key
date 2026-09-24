import pytest


@pytest.fixture(scope="module")
def api_key(test_app, admin_key):
    resp = test_app.post_json(
        "/api/v1/api-keys",
        {"name": "tickets-test-client"},
        headers={"X-Admin-Key": admin_key},
    )
    return resp.json["api_key"]


@pytest.fixture(scope="module")
def other_api_key(test_app, admin_key):
    resp = test_app.post_json(
        "/api/v1/api-keys",
        {"name": "other-client"},
        headers={"X-Admin-Key": admin_key},
    )
    return resp.json["api_key"]


def test_health(test_app):
    resp = test_app.get("/health")
    assert resp.status_code == 200
    assert resp.json["status"] == "ok"


def test_create_ticket_requires_api_key(test_app):
    resp = test_app.post_json(
        "/api/v1/tickets", {"title": "no key"}, expect_errors=True
    )
    assert resp.status_code == 401


def test_create_ticket_missing_title(test_app, api_key):
    resp = test_app.post_json(
        "/api/v1/tickets",
        {"description": "no title"},
        headers={"X-API-Key": api_key},
        expect_errors=True,
    )
    assert resp.status_code == 422


def test_ticket_crud_flow(test_app, api_key):
    resp = test_app.post_json(
        "/api/v1/tickets",
        {"title": "Printer broken", "description": "It jams every time"},
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 201
    ticket = resp.json
    assert ticket["status"] == "OPEN"
    ticket_id = ticket["id"]

    resp = test_app.get("/api/v1/tickets", headers={"X-API-Key": api_key})
    assert resp.status_code == 200
    body = resp.json
    assert "items" in body and "total" in body and "limit" in body and "offset" in body
    assert any(t["id"] == ticket_id for t in body["items"])

    resp = test_app.get(
        "/api/v1/tickets/%s" % ticket_id, headers={"X-API-Key": api_key}
    )
    assert resp.status_code == 200
    assert resp.json["id"] == ticket_id

    resp = test_app.put_json(
        "/api/v1/tickets/%s" % ticket_id,
        {"title": "Printer still broken", "description": "Updated details"},
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 200
    assert resp.json["title"] == "Printer still broken"

    resp = test_app.patch_json(
        "/api/v1/tickets/%s/status" % ticket_id,
        {"status": "RESOLVED"},
        headers={"X-API-Key": api_key},
        expect_errors=True,
    )
    assert resp.status_code == 422

    resp = test_app.patch_json(
        "/api/v1/tickets/%s/status" % ticket_id,
        {"status": "IN_PROGRESS"},
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 200
    assert resp.json["status"] == "IN_PROGRESS"

    resp = test_app.patch_json(
        "/api/v1/tickets/%s/status" % ticket_id,
        {"status": "RESOLVED"},
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 200
    assert resp.json["status"] == "RESOLVED"

    resp = test_app.patch_json(
        "/api/v1/tickets/%s/status" % ticket_id,
        {"status": "IN_PROGRESS"},
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 200
    assert resp.json["status"] == "IN_PROGRESS"

    resp = test_app.delete(
        "/api/v1/tickets/%s" % ticket_id, headers={"X-API-Key": api_key}
    )
    assert resp.status_code == 204

    resp = test_app.get(
        "/api/v1/tickets/%s" % ticket_id,
        headers={"X-API-Key": api_key},
        expect_errors=True,
    )
    assert resp.status_code == 404


def test_ticket_isolation_between_clients(test_app, api_key, other_api_key):
    resp = test_app.post_json(
        "/api/v1/tickets",
        {"title": "Client A ticket"},
        headers={"X-API-Key": api_key},
    )
    ticket_id = resp.json["id"]

    resp = test_app.get(
        "/api/v1/tickets/%s" % ticket_id,
        headers={"X-API-Key": other_api_key},
        expect_errors=True,
    )
    assert resp.status_code == 404


def test_docs_and_schema(test_app):
    resp = test_app.get("/api/v1/schema")
    assert resp.status_code == 200
    assert resp.json["openapi"] == "3.0.0"

    resp = test_app.get("/api/v1/openapi.json")
    assert resp.status_code == 200

    resp = test_app.get("/api/v1/docs")
    assert resp.status_code == 200
    assert "swagger" in resp.text.lower()
