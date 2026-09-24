import json

import bottle

from app.database import get_session
from app.kafka_producer import publish_ticket_resolved
from app.models import TICKET_STATUSES, SupportTicket
from app.utils import require_api_key

# Allowed status transitions. OPEN -> IN_PROGRESS -> RESOLVED,
# with reopening a resolved ticket back to IN_PROGRESS being allowed.
ALLOWED_TRANSITIONS = {
    "OPEN": {"IN_PROGRESS"},
    "IN_PROGRESS": {"RESOLVED"},
    "RESOLVED": {"IN_PROGRESS"},
}


def _get_owned_ticket(session, ticket_id, client_id):
    ticket = (
        session.query(SupportTicket)
        .filter(SupportTicket.id == ticket_id, SupportTicket.client_id == client_id)
        .first()
    )
    if not ticket:
        bottle.abort(404, "Ticket not found")
    return ticket


def register_ticket_routes(app):
    @app.post("/api/v1/tickets")
    @require_api_key
    def create_ticket():
        try:
            data = bottle.request.json or {}
        except Exception:
            bottle.abort(400, "Invalid JSON body")

        title = (data or {}).get("title")
        description = (data or {}).get("description")

        if not title or not isinstance(title, str):
            bottle.abort(422, "Field 'title' is required")

        session = get_session()
        ticket = SupportTicket(
            title=title,
            description=description,
            status="OPEN",
            client_id=bottle.request.client_id,
        )
        session.add(ticket)
        session.commit()

        bottle.response.content_type = "application/json"
        bottle.response.status = 201
        return json.dumps(ticket.to_dict())

    @app.get("/api/v1/tickets")
    @require_api_key
    def list_tickets():
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

        base_query = session.query(SupportTicket).filter(
            SupportTicket.client_id == bottle.request.client_id
        )
        total = base_query.count()
        rows = (
            base_query.order_by(SupportTicket.id.desc()).offset(offset).limit(limit).all()
        )

        items = [t.to_dict() for t in rows]

        bottle.response.content_type = "application/json"
        return json.dumps({"items": items, "total": total, "limit": limit, "offset": offset})

    @app.get("/api/v1/tickets/<ticket_id:int>")
    @require_api_key
    def get_ticket(ticket_id):
        session = get_session()
        ticket = _get_owned_ticket(session, ticket_id, bottle.request.client_id)

        bottle.response.content_type = "application/json"
        return json.dumps(ticket.to_dict())

    @app.put("/api/v1/tickets/<ticket_id:int>")
    @require_api_key
    def update_ticket(ticket_id):
        session = get_session()
        ticket = _get_owned_ticket(session, ticket_id, bottle.request.client_id)

        try:
            data = bottle.request.json or {}
        except Exception:
            bottle.abort(400, "Invalid JSON body")

        title = (data or {}).get("title")
        description = (data or {}).get("description")

        if not title or not isinstance(title, str):
            bottle.abort(422, "Field 'title' is required")

        ticket.title = title
        ticket.description = description
        session.commit()

        bottle.response.content_type = "application/json"
        return json.dumps(ticket.to_dict())

    @app.patch("/api/v1/tickets/<ticket_id:int>/status")
    @require_api_key
    def change_ticket_status(ticket_id):
        session = get_session()
        ticket = _get_owned_ticket(session, ticket_id, bottle.request.client_id)

        try:
            data = bottle.request.json or {}
        except Exception:
            bottle.abort(400, "Invalid JSON body")

        new_status = (data or {}).get("status")
        if not new_status or new_status not in TICKET_STATUSES:
            bottle.abort(422, "Field 'status' must be one of: " + ", ".join(TICKET_STATUSES))

        current_status = ticket.status
        if new_status == current_status:
            bottle.abort(422, "Ticket is already in status '%s'" % current_status)

        allowed = ALLOWED_TRANSITIONS.get(current_status, set())
        if new_status not in allowed:
            bottle.abort(
                422,
                "Invalid status transition from '%s' to '%s'" % (current_status, new_status),
            )

        ticket.status = new_status
        session.commit()

        if new_status == "RESOLVED":
            publish_ticket_resolved(ticket)

        bottle.response.content_type = "application/json"
        return json.dumps(ticket.to_dict())

    @app.delete("/api/v1/tickets/<ticket_id:int>")
    @require_api_key
    def delete_ticket(ticket_id):
        session = get_session()
        ticket = _get_owned_ticket(session, ticket_id, bottle.request.client_id)

        session.delete(ticket)
        session.commit()

        bottle.response.status = 204
        return ""
