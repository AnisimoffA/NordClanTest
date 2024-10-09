from sqlalchemy import Column, Integer, String, JSON, TIMESTAMP
from .database import Base


class ScoreModel(Base):
    __tablename__ = 'scores'
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)

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
