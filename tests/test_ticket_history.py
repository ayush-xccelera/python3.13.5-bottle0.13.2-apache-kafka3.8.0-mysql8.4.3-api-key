import pytest


@pytest.fixture(scope="module")
def api_key(test_app, admin_key):
    resp = test_app.post_json(
        "/api/v1/api-keys",
        {"name": "history-test-client"},
        headers={"X-Admin-Key": admin_key},
    )
    return resp.json["api_key"]


@pytest.fixture(scope="module")
def other_api_key(test_app, admin_key):
    resp = test_app.post_json(
        "/api/v1/api-keys",
        {"name": "history-other-client"},
        headers={"X-Admin-Key": admin_key},
    )
    return resp.json["api_key"]


def test_ticket_history_tracks_transitions(test_app, api_key):
    resp = test_app.post_json(
        "/api/v1/tickets",
        {"title": "History ticket", "description": "test history"},
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 201
    ticket_id = resp.json["id"]

    # No transitions yet -> empty history.
    resp = test_app.get(
        "/api/v1/tickets/%s/history" % ticket_id, headers={"X-API-Key": api_key}
    )
    assert resp.status_code == 200
    assert resp.json["items"] == []
    assert resp.json["total"] == 0

    # Updating (PUT) the ticket must NOT create history.
    resp = test_app.put_json(
        "/api/v1/tickets/%s" % ticket_id,
        {"title": "Updated title", "description": "still no history"},
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 200

    resp = test_app.get(
        "/api/v1/tickets/%s/history" % ticket_id, headers={"X-API-Key": api_key}
    )
    assert resp.status_code == 200
    assert resp.json["total"] == 0

    # A rejected transition must NOT create a history record.
    resp = test_app.patch_json(
        "/api/v1/tickets/%s/status" % ticket_id,
        {"status": "RESOLVED"},
        headers={"X-API-Key": api_key},
        expect_errors=True,
    )
    assert resp.status_code == 422

    resp = test_app.get(
        "/api/v1/tickets/%s/history" % ticket_id, headers={"X-API-Key": api_key}
    )
    assert resp.json["total"] == 0

    # A successful transition creates exactly one history record.
    resp = test_app.patch_json(
        "/api/v1/tickets/%s/status" % ticket_id,
        {"status": "IN_PROGRESS"},
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 200

    resp = test_app.get(
        "/api/v1/tickets/%s/history" % ticket_id, headers={"X-API-Key": api_key}
    )
    assert resp.status_code == 200
    body = resp.json
    assert body["total"] == 1
    record = body["items"][0]
    assert record["ticket_id"] == ticket_id
    assert record["previous_status"] == "OPEN"
    assert record["new_status"] == "IN_PROGRESS"
    assert "changed_at" in record

    # Another successful transition adds a second record.
    resp = test_app.patch_json(
        "/api/v1/tickets/%s/status" % ticket_id,
        {"status": "RESOLVED"},
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 200

    resp = test_app.get(
        "/api/v1/tickets/%s/history" % ticket_id, headers={"X-API-Key": api_key}
    )
    body = resp.json
    assert body["total"] == 2
    assert body["items"][1]["previous_status"] == "IN_PROGRESS"
    assert body["items"][1]["new_status"] == "RESOLVED"


def test_ticket_history_requires_api_key(test_app, api_key):
    resp = test_app.post_json(
        "/api/v1/tickets",
        {"title": "No-key history ticket"},
        headers={"X-API-Key": api_key},
    )
    ticket_id = resp.json["id"]

    resp = test_app.get(
        "/api/v1/tickets/%s/history" % ticket_id, expect_errors=True
    )
    assert resp.status_code == 401


def test_ticket_history_only_owning_client(test_app, api_key, other_api_key):
    resp = test_app.post_json(
        "/api/v1/tickets",
        {"title": "Owner-only history ticket"},
        headers={"X-API-Key": api_key},
    )
    ticket_id = resp.json["id"]

    resp = test_app.get(
        "/api/v1/tickets/%s/history" % ticket_id,
        headers={"X-API-Key": other_api_key},
        expect_errors=True,
    )
    assert resp.status_code == 404
