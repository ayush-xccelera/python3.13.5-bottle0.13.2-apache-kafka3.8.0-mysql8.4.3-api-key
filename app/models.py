import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_hash = Column(String(128), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)

    tickets = relationship("SupportTicket", back_populates="client", cascade="all, delete-orphan")


TICKET_STATUSES = ("OPEN", "IN_PROGRESS", "RESOLVED")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="OPEN")
    client_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    client = relationship("ApiKey", back_populates="tickets")
    status_history = relationship(
        "TicketStatusHistory", back_populates="ticket", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "client_id": self.client_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TicketStatusHistory(Base):
    __tablename__ = "ticket_status_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(
        Integer, ForeignKey("support_tickets.id"), nullable=False, index=True
    )
    previous_status = Column(String(20), nullable=False)
    new_status = Column(String(20), nullable=False)
    changed_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    ticket = relationship("SupportTicket", back_populates="status_history")

    def to_dict(self):
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "previous_status": self.previous_status,
            "new_status": self.new_status,
            "changed_at": self.changed_at.isoformat() if self.changed_at else None,
        }
