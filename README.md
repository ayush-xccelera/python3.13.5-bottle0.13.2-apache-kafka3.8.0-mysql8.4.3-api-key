# Support Ticket API

A Bottle (WSGI) backend implementing a multi-tenant support ticket system,
authenticated via API keys, with MySQL persistence and a Kafka event
notification on ticket resolution.

## Stack

- Python 3.13.5
- Bottle 0.13.2
- SQLAlchemy 2.x + Alembic (MySQL via PyMySQL)
- gunicorn (Linux/macOS) / waitress (Windows)
- kafka-python (publishes `TICKET_RESOLVED` events to topic `ticket-events`)

## Entities

- **Client** — identified solely by its API key (`ApiKey` model).
- **Support Ticket** — belongs to exactly one client; status lifecycle
  `OPEN -> IN_PROGRESS -> RESOLVED`, with `RESOLVED -> IN_PROGRESS` allowed
  as a "reopen".

## Auth

- Business endpoints (`/api/v1/tickets/*`) require header `X-API-Key`.
- Admin endpoints (`/api/v1/api-keys*`) require header `X-Admin-Key`,
  compared against `ADMIN_API_KEY` from the environment.

## Running locally

1. Copy `.env.example` to `.env_99bee2c7-edf1-4806-8469-e0e5dc0f680f` and fill in values
   (already provided for this generated project).
2. Create a virtualenv and install dependencies:
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run database migrations:
   ```
   alembic upgrade head
   ```
4. Start the server:
   ```
   chmod +x start.sh
   PORT=20823 ./start.sh
   ```
   (Windows: `start.bat`)

The server listens on `http://localhost:20823`.

## Running via Docker

```
docker build -t support-ticket-api .
docker run --env-file .env_99bee2c7-edf1-4806-8469-e0e5dc0f680f -p 20823:20823 support-ticket-api
```

## Creating your first API key

Admin routes are gated by `ADMIN_API_KEY` (see the env file). Example:

```
curl -X POST http://localhost:20823/api/v1/api-keys \
  -H "X-Admin-Key: <ADMIN_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"name": "acme-corp"}'
```

The response contains the **raw API key** — store it now, it is never shown again.
Use it as `X-API-Key` on all `/api/v1/tickets` requests.

## API Endpoints

| Method | Path                              | Auth        | Description                          |
|--------|------------------------------------|-------------|---------------------------------------|
| GET    | /health                            | none        | Health check                          |
| POST   | /api/v1/api-keys                   | X-Admin-Key | Create an API key                     |
| GET    | /api/v1/api-keys                   | X-Admin-Key | List API keys (paginated)             |
| DELETE | /api/v1/api-keys/{id}              | X-Admin-Key | Revoke an API key                     |
| POST   | /api/v1/tickets                    | X-API-Key   | Create a ticket                       |
| GET    | /api/v1/tickets                    | X-API-Key   | List own tickets (paginated)          |
| GET    | /api/v1/tickets/{id}                | X-API-Key   | Retrieve a ticket                     |
| PUT    | /api/v1/tickets/{id}                | X-API-Key   | Update title/description              |
| PATCH  | /api/v1/tickets/{id}/status         | X-API-Key   | Change ticket status                  |
| DELETE | /api/v1/tickets/{id}                | X-API-Key   | Delete a ticket                       |
| GET    | /api/v1/docs                       | none        | Swagger UI                            |
| GET    | /api/v1/schema                     | none        | OpenAPI 3.0 JSON spec                 |
| GET    | /api/v1/openapi.json               | none        | OpenAPI 3.0 JSON spec (alias)         |

## Pagination

List endpoints accept `?limit=&offset=` (default `limit=20`, max `100`) and
return `{"items": [...], "total": <int>, "limit": <int>, "offset": <int>}`.

## Kafka

When a ticket transitions to `RESOLVED`, a `TICKET_RESOLVED` JSON event is
published to the `ticket-events` topic on `KAFKA_BOOTSTRAP_SERVERS`
(default `localhost:9092`). This project only produces to this topic; it does
not consume any topic.

## Tests

```
pip install pytest webtest
pytest tests/ -v
```
