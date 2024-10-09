from sqlalchemy import Column, Integer, String, DateTime, JSON, TIMESTAMP
from .database import Base


class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    deadline = Column(DateTime, nullable=False)
    score_status = Column(String(100), default="в обработке")

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class OutboxMessageModel(Base):
    __tablename__ = "outbox_messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    occurred_on = Column(TIMESTAMP(timezone=True), nullable=False)
    status = Column(String, nullable=False)
    data = Column(JSON, nullable=False)
    processed_on = Column(TIMESTAMP(timezone=True))

    def __str__(self) -> str:
        return (
            f"OutboxMessage(id={self.id}, occurred_on={self.occurred_on}, "
            f"type={self.type}, processed_on={self.processed_on})"
        )
