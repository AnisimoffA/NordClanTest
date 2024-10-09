from enum import Enum
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class EventStatus(str, Enum):
    IN_PROGRESS = "в обработке"
    HIGH_SCORE = "оценено высокой оценкой"
    LOW_SCORE = "оценено низкой оценкой"


class Event(BaseModel):
    id: str
    title: str
    deadline: datetime
    status: EventStatus = EventStatus.IN_PROGRESS


class EventCreate(BaseModel):
    title: str
    deadline: datetime
    status: EventStatus = EventStatus.IN_PROGRESS


class KafkaEvent(BaseModel):
    data: Optional[dict]
    event: str
    status: str
