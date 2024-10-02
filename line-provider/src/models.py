from sqlalchemy import Column, Integer, String, DateTime
from .database import Base


class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    deadline = Column(DateTime, nullable=False)
    score_status = Column(String(100), default="в обработке")

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


