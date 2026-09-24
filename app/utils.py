import datetime
import hashlib
import secrets
from functools import wraps

import bottle

from app.config import config
from app.database import get_session
from app.models import ApiKey


def generate_api_key():
    """Generate a new raw API key and its sha256 hash.

    Returns a tuple (raw_key, key_hash).
    """
    raw_key = secrets.token_urlsafe(32)
    key_hash = hash_api_key(raw_key)
    return raw_key, key_hash


def hash_api_key(raw_key):
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        raw_key = bottle.request.headers.get("X-API-Key")
        if not raw_key:
            bottle.abort(401, "Missing X-API-Key header")

        session = get_session()
        key_hash = hash_api_key(raw_key)
        api_key = (
            session.query(ApiKey)
            .filter(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True))
            .first()
        )
        if not api_key:
            bottle.abort(401, "Invalid or inactive API key")

        api_key.last_used_at = datetime.datetime.utcnow()
        session.commit()

        bottle.request.api_key = api_key
        bottle.request.client_id = api_key.id
        return func(*args, **kwargs)

    return wrapper


def require_admin_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        admin_key = bottle.request.headers.get("X-Admin-Key")
        if not admin_key or not config.ADMIN_API_KEY:
            bottle.abort(401, "Missing X-Admin-Key header")
        if not secrets.compare_digest(admin_key, config.ADMIN_API_KEY):
            bottle.abort(401, "Invalid admin key")
        return func(*args, **kwargs)

    return wrapper
