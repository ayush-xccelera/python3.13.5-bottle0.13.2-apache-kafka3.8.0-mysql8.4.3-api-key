import os

from dotenv import load_dotenv

load_dotenv(".env_ca1491da06cbaa95", override=True)


class Config:
    DATABASE_URL = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://myuser:mypassword@localhost:3306/gen_30feae450dd1",
    )
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-me-too")
    ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "")
    PORT = int(os.environ.get("PORT", 20823))
    KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_TICKET_EVENTS_TOPIC = os.environ.get("KAFKA_TICKET_EVENTS_TOPIC", "ticket-events")


config = Config()
