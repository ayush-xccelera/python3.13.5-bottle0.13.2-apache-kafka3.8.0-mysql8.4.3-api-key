COMMIT_MESSAGE: Add TicketStatusHistory tracking with Kafka TICKET_STATUS_CHANGED event, consumer, and history endpoint

## Features Added
- New `TicketStatusHistory` entity (`id`, `ticket_id`, `previous_status`, `new_status`, `changed_at`) recording every successful ticket status transition.
- On every successful status transition, a `TICKET_STATUS_CHANGED` Kafka event is published to the ticket-events topic (existing `TICKET_RESOLVED` event on resolution is preserved unchanged).
- New Kafka consumer module (`app/kafka_consumer.py`) that persists `TICKET_STATUS_CHANGED` events into `TicketStatusHistory`. Its `persist_status_change` handler is shared and called synchronously by the ticket-status route right after a successful transition, so the history record is guaranteed to exist immediately even when no live Kafka broker is reachable in this environment (the standalone consumer, runnable via `python -m app.kafka_consumer`, uses the exact same handler for real Kafka-driven persistence in a deployed multi-broker setup).
- New endpoint `GET /api/v1/tickets/{id}/history` — requires `X-API-Key`, returns a paginated (`limit`/`offset`, matching the existing project convention) list of the ticket's status-change history, restricted to the ticket's owning client (returns 404 for tickets owned by a different client, matching the existing ownership-check pattern used by other ticket routes).
- Rejected status transitions (invalid transition, same-status, missing/invalid status) do not create any history record.
- Creating or updating (PUT) a ticket does not create history records — only the `PATCH .../status` transition does.
- Original ticket CRUD/lifecycle behavior is unchanged.

## Files Modified
- `app/models.py` — added `TicketStatusHistory` model and `SupportTicket.status_history` relationship.
- `app/routes/tickets.py` — on successful status change: publish `TICKET_STATUS_CHANGED` event and persist history record; added `GET /api/v1/tickets/<id>/history` endpoint.
- `app/kafka_producer.py` — added `publish_ticket_status_changed(ticket, previous_status, new_status)`; added `.env_ca1491da06cbaa95` dotenv loading.
- `app/config.py` — fixed dotenv path to load the project's actual env file `.env_ca1491da06cbaa95` (was pointing at a stale filename from a previous session).

## Files Added
- `app/kafka_consumer.py` — TICKET_STATUS_CHANGED consumer: `persist_status_change`, `handle_message`, `run_consumer` (standalone process entrypoint).
- `alembic/versions/a1b2c3d4e5f6_add_ticket_status_history.py` — migration creating the `ticket_status_history` table.
- `tests/test_ticket_history.py` — tests for the new history endpoint, auth requirement, ownership restriction, and the correctness rules (no history on PUT, no history on rejected transition, one record per successful transition).

## Secrets Extracted
- No new hardcoded secrets found in the added code. `ADMIN_API_KEY` (pre-existing) and Kafka/DB settings are all sourced via `os.environ`/`.env_ca1491da06cbaa95` as before; a working `ADMIN_API_KEY` value was written to `.env_ca1491da06cbaa95` for local testing.

## DB URLs Resolved
- `mysql+pymysql://myuser:mypassword@localhost:3306/gen_30feae450dd1` -> unchanged (pre-resolved / already working), written to `.env_ca1491da06cbaa95` as `DATABASE_URL`.

## Test Results Summary
12 PASSED, 0 FAILED, 0 SKIPPED (9 pre-existing tests in `tests/test_auth.py` + `tests/test_tickets.py`, plus 3 new tests in `tests/test_ticket_history.py`). Endpoints additionally verified live via curl against a running gunicorn server on port 23254, confirming: empty history before any transition, 401 with no API key, 404 for a non-owning client, no history created by PUT or by a rejected transition, and exactly one history record per successful transition with accurate previous/new status.
