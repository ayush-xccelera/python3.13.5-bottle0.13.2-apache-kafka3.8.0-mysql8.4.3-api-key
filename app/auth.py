import json

import bottle

from app.database import get_session
from app.models import ApiKey
from app.utils import generate_api_key, require_admin_key


def register_auth_routes(app):
    @app.post("/api/v1/api-keys")
    @require_admin_key
    def create_api_key():
        try:
            data = bottle.request.json or {}
        except Exception:
            bottle.abort(400, "Invalid JSON body")

        name = (data or {}).get("name")
        if not name or not isinstance(name, str):
            bottle.abort(422, "Field 'name' is required")

        raw_key, key_hash = generate_api_key()

        session = get_session()
        api_key = ApiKey(key_hash=key_hash, name=name, is_active=True)
        session.add(api_key)
        session.commit()

        bottle.response.content_type = "application/json"
        bottle.response.status = 201
        return json.dumps(
            {
                "id": api_key.id,
                "name": api_key.name,
                "api_key": raw_key,
                "is_active": api_key.is_active,
                "created_at": api_key.created_at.isoformat(),
            }
        )

    @app.get("/api/v1/api-keys")
    @require_admin_key
    def list_api_keys():
        session = get_session()

        limit = bottle.request.query.get("limit", 20)
        offset = bottle.request.query.get("offset", 0)
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 20
        try:
            offset = int(offset)
        except (TypeError, ValueError):
            offset = 0
        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        total = session.query(ApiKey).count()
        rows = session.query(ApiKey).order_by(ApiKey.id).offset(offset).limit(limit).all()

        items = [
            {
                "id": k.id,
                "name": k.name,
                "is_active": k.is_active,
                "created_at": k.created_at.isoformat() if k.created_at else None,
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            }
            for k in rows
        ]

        bottle.response.content_type = "application/json"
        return json.dumps({"items": items, "total": total, "limit": limit, "offset": offset})

    @app.delete("/api/v1/api-keys/<key_id:int>")
    @require_admin_key
    def revoke_api_key(key_id):
        session = get_session()
        api_key = session.query(ApiKey).filter(ApiKey.id == key_id).first()
        if not api_key:
            bottle.abort(404, "API key not found")

        api_key.is_active = False
        session.commit()

        bottle.response.content_type = "application/json"
        return json.dumps({"id": api_key.id, "is_active": api_key.is_active})

    @app.get("/health")
    def health():
        bottle.response.content_type = "application/json"
        return json.dumps({"status": "ok"})
