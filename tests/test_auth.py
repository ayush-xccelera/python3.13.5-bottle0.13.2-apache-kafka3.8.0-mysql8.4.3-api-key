def test_create_api_key_requires_admin(test_app):
    resp = test_app.post_json(
        "/api/v1/api-keys", {"name": "no-admin-header"}, expect_errors=True
    )
    assert resp.status_code == 401


def test_create_api_key_wrong_admin(test_app):
    resp = test_app.post_json(
        "/api/v1/api-keys",
        {"name": "wrong-admin"},
        headers={"X-Admin-Key": "wrong-key"},
        expect_errors=True,
    )
    assert resp.status_code == 401


def test_create_list_revoke_api_key(test_app, admin_key):
    resp = test_app.post_json(
        "/api/v1/api-keys",
        {"name": "test-client"},
        headers={"X-Admin-Key": admin_key},
    )
    assert resp.status_code == 201
    body = resp.json
    assert "api_key" in body
    key_id = body["id"]

    resp = test_app.get(
        "/api/v1/api-keys", headers={"X-Admin-Key": admin_key}
    )
    assert resp.status_code == 200
    listed = resp.json
    assert "items" in listed
    assert "total" in listed
    assert any(item["id"] == key_id for item in listed["items"])

    resp = test_app.delete(
        "/api/v1/api-keys/%s" % key_id, headers={"X-Admin-Key": admin_key}
    )
    assert resp.status_code == 200
    assert resp.json["is_active"] is False
