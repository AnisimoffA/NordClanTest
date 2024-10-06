import aiohttp
from fastapi.exceptions import HTTPException
from dateutil import parser
from datetime import datetime, timezone
from sqlalchemy import select
from .database import async_session_maker
from .models import ScoreModel
from .config import LP_URL, LP_PORT
from sqlalchemy.ext.asyncio import AsyncSession


class EventUsefulMethods:
    def to_utc_time(current_deadline):
        correct_deadline = parser.isoparse(current_deadline)
        return correct_deadline.replace(tzinfo=timezone.utc)


class EventRemoteMethods:
    @staticmethod
    async def fetch_from_service(url: str):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise HTTPException(
                            status_code=response.status,
                            detail="Ошибка при получении данных"
                        )
                    return await response.json()
            except aiohttp.ClientError:
                raise HTTPException(
                    status_code=500,
                    detail="Ошибка коммуникации с внешним сервисом"
                )

    @staticmethod
    async def get_all_events():
        return await EventRemoteMethods.fetch_from_service(
            f"http://{LP_URL}:{LP_PORT}/events"
        )

    @staticmethod
    async def get_event_by_id(event_id: int):
        return await EventRemoteMethods.fetch_from_service(
            f"http://{LP_URL}:{LP_PORT}/events/{event_id}"
        )


class ScoreDBMethods:
    @staticmethod
    async def _get_session() -> AsyncSession:
        async with async_session_maker() as session:
            return session

    @staticmethod
    async def select_all_from_score():
        async with await ScoreDBMethods._get_session() as session:
            query = select(ScoreModel)
            result = await session.execute(query)
            scores = result.scalars().all()
            return scores

    @staticmethod
    async def insert_into_score(event_id: int, score: int):
        new_score = ScoreModel(event_id=event_id, score=score)
        async with await ScoreDBMethods._get_session() as session:
            session.add(new_score)
            await session.commit()
            await session.refresh(new_score)
            return new_score.id

    @staticmethod
    async def delete_from_score(row_id: int):
        async with await ScoreDBMethods._get_session() as session:
            result = await session.execute(
                select(ScoreModel)
                .where(ScoreModel.id == row_id)
            )
            score_row = result.scalar_one()
            await session.delete(score_row)
            await session.commit()


class EventValidator:
    @staticmethod
    def validate_deadline(deadline):
        if deadline < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Событие нельзя оценить")


class ScoreMethods:
    @staticmethod
    def check_actuality(events):
        returned_events = []
        for event in events:
            deadline = parser.isoparse(event["deadline"])
            deadline = deadline.replace(tzinfo=timezone.utc)
            if deadline > datetime.now(timezone.utc):
                returned_events.append(event)
        return returned_events

