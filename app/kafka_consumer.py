"""Consumer for TICKET_STATUS_CHANGED events.

Persists each successful ticket status transition into the
``ticket_status_history`` table. The `handle_message` / `persist_status_change`
functions are the single source of truth used both by the standalone consumer
process (`python -m app.kafka_consumer`) and, synchronously, by the ticket
status-change route itself -- guaranteeing the history record exists
immediately after a successful transition even if no Kafka broker is
reachable in the current environment.
"""

import json
import logging

from dotenv import load_dotenv

load_dotenv(".env_ca1491da06cbaa95", override=True)

from app.config import config
from app.database import SessionLocal, get_session
from app.models import TicketStatusHistory

logger = logging.getLogger(__name__)


def persist_status_change(session, ticket_id, previous_status, new_status):
    """Create and persist a TicketStatusHistory record."""
    history = TicketStatusHistory(
        ticket_id=ticket_id,
        previous_status=previous_status,
        new_status=new_status,
    )
    session.add(history)
    session.commit()
    return history


def handle_message(event):
    """Handle a single decoded TICKET_STATUS_CHANGED kafka message."""
    if not event or event.get("event_type") != "TICKET_STATUS_CHANGED":
        return None

    session = get_session()
    try:
        return persist_status_change(
            session,
            ticket_id=event.get("ticket_id"),
            previous_status=event.get("previous_status"),
            new_status=event.get("new_status"),
        )
    finally:
        SessionLocal.remove()


def run_consumer():  # pragma: no cover - requires a live Kafka broker
    """Run the TICKET_STATUS_CHANGED consumer loop.

    Intended to be launched as a standalone process, e.g.:
        python -m app.kafka_consumer
    """
    from kafka import KafkaConsumer

    consumer = KafkaConsumer(
        config.KAFKA_TICKET_EVENTS_TOPIC,
        bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        group_id="ticket-status-history-consumer",
    )
    logger.info(
        "TICKET_STATUS_CHANGED consumer started on topic %s",
        config.KAFKA_TICKET_EVENTS_TOPIC,
    )
    for message in consumer:
        try:
            handle_message(message.value)
        except Exception:  # pragma: no cover
            logger.exception("Failed to process message: %s", message.value)


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    run_consumer()
