import datetime
import json
import logging

from dotenv import load_dotenv

load_dotenv(".env_ca1491da06cbaa95", override=True)

from app.config import config

logger = logging.getLogger(__name__)

_producer = None
_producer_init_attempted = False


def _get_producer():
    global _producer, _producer_init_attempted
    if _producer is not None:
        return _producer
    if _producer_init_attempted:
        return None
    _producer_init_attempted = True
    try:
        from kafka import KafkaProducer

        _producer = KafkaProducer(
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            retries=3,
        )
    except Exception as exc:  # pragma: no cover - kafka may be unavailable
        logger.warning("Kafka producer unavailable: %s", exc)
        _producer = None
    return _producer


def publish_ticket_resolved(ticket):
    """Publish a TICKET_RESOLVED event to the ticket-events topic."""
    producer = _get_producer()
    event = {
        "event_type": "TICKET_RESOLVED",
        "ticket_id": ticket.id,
        "client_id": ticket.client_id,
        "title": ticket.title,
        "status": ticket.status,
        "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
    }
    if producer is None:
        logger.warning("Kafka producer not available, event not published: %s", event)
        return False
    try:
        producer.send(config.KAFKA_TICKET_EVENTS_TOPIC, value=event)
        producer.flush(timeout=5)
        return True
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to publish TICKET_RESOLVED event: %s", exc)
        return False


def publish_ticket_status_changed(ticket, previous_status, new_status):
    """Publish a TICKET_STATUS_CHANGED event to the ticket-events topic.

    Fired on every successful ticket status transition.
    """
    producer = _get_producer()
    event = {
        "event_type": "TICKET_STATUS_CHANGED",
        "ticket_id": ticket.id,
        "client_id": ticket.client_id,
        "previous_status": previous_status,
        "new_status": new_status,
        "changed_at": datetime.datetime.utcnow().isoformat(),
    }
    if producer is None:
        logger.warning("Kafka producer not available, event not published: %s", event)
        return False
    try:
        producer.send(config.KAFKA_TICKET_EVENTS_TOPIC, value=event)
        producer.flush(timeout=5)
        return True
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to publish TICKET_STATUS_CHANGED event: %s", exc)
        return False
