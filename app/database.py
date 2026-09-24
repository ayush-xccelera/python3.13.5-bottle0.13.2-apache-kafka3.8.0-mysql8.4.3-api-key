from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

from app.config import config

engine = create_engine(config.DATABASE_URL, echo=False, pool_pre_ping=True)

SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))

Base = declarative_base()


def init_db():
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()
