from sqlalchemy import Column, Integer, String
from .database import Base


class ScoreModel(Base):
    __tablename__ = 'scores'
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
