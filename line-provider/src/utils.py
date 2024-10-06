import aiohttp
from fastapi.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
from sqlalchemy import select
from .database import async_session_maker
from .models import Event
from .schemas import EventStatus, EventCreate
from sqlalchemy.ext.asyncio import AsyncSession


class EventUsefulMethods:
    @staticmethod
    def to_utc_time(current_deadline):
        correct_deadline = current_deadline.astimezone(timezone.utc).replace(tzinfo=None)
        return correct_deadline


class EventDBMethods:
    @staticmethod
    async def _get_session() -> AsyncSession:
        async with async_session_maker() as session:
            return session

    @staticmethod
    async def select_all_events():
        async with await EventDBMethods._get_session() as session:
            query = select(Event)
            result = await session.execute(query)
            scores = result.scalars().all()
            return scores

    @staticmethod
    async def select_event_by_id(event_id: int):
        async with await EventDBMethods._get_session() as session:
            result = await session.execute(
                select(Event).
                where(Event.id == event_id)
            )
            event = result.scalars().first()

            if event is None:
                raise HTTPException(status_code=404, detail="Событие не найдено")
            return event

    @staticmethod
    async def update_event_status(event_id: str, status: EventStatus):
        async with await EventDBMethods._get_session() as session:
            result = await session.execute(
                select(Event).
                where(Event.id == event_id)
            )
            event = result.scalars().first()
            if event:
                event.score_status = status
                await session.commit()

    @staticmethod
    async def insert_into_event(event: EventCreate, deadline: datetime):
        new_event = Event(title=event.title, deadline=deadline)
        async with await EventDBMethods._get_session() as session:
            session.add(new_event)
            try:
                await session.commit()
                await session.refresh(new_event)
            except IntegrityError:
                await session.rollback()
                raise HTTPException(
                    status_code=400,
                    detail="Ошибка при добавлении события"
                )