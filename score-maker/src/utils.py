import aiohttp
import json
from fastapi.exceptions import HTTPException
from dateutil import parser
from datetime import datetime, timezone
from sqlalchemy import select
from .database import async_session_maker
from .models import ScoreModel, OutboxMessageModel
from .config import LP_URL, LP_PORT
from .schemas import KafkaEvent
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
        async with await ScoreDBMethods._get_session() as session:
            try:
                new_score = ScoreModel(event_id=event_id, score=score)
                session.add(new_score)
                await session.commit()
                await session.refresh(new_score)
                row_id = new_score.id

                data = KafkaEvent(
                    data={
                        "event_id": event_id,
                        "event_score": score,
                        "row_id": row_id
                    },
                    event="score_insert_into_db",
                    status="success"
                )

                new_event = OutboxMessageModel(
                    occurred_on=datetime.now(timezone.utc),
                    status="in process",
                    data=json.dumps(data.dict())
                )
                session.add(new_event)
                await session.commit()
                return {"status": "success"}

            except Exception as e:
                await session.rollback()
                return {"status": "failed", "error": e}

    @staticmethod
    async def delete_from_score(row_id: int):
        async with await ScoreDBMethods._get_session() as session:
            result = await session.execute(
                select(ScoreModel)
                .where(ScoreModel.id == row_id)
            )
            score_row = result.scalar_one_or_none()

            # Проверяем, что запись найдена
            if score_row is None:
                print(f"No score found with id: {row_id}")
            await session.delete(score_row)
            await session.commit()


class EventValidator:
    @staticmethod
    def validate_deadline(deadline):
        if deadline < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400,
                detail="Событие нельзя оценить")


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
