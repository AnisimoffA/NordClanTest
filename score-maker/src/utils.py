import aiohttp
from fastapi.exceptions import HTTPException
from dateutil import parser
from datetime import datetime, timezone
from sqlalchemy import select
from .database import async_session_maker
from .models import ScoreModel
from .config import LP_URL, LP_PORT


class EventMethods:
    HIGH_SCORE = "оценено высокой оценкой"
    LOW_SCORE = "оценено низкой оценкой"

    def to_utc_time(current_deadline):
        correct_deadline = parser.isoparse(current_deadline)
        return correct_deadline.replace(tzinfo=timezone.utc)

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
        return await EventMethods.fetch_from_service(
            f"http://{LP_URL}:{LP_PORT}/events"
        )

    @staticmethod
    async def get_event_by_id(event_id: int):
        return await EventMethods.fetch_from_service(
            f"http://{LP_URL}:{LP_PORT}/events/{event_id}"
        )

    @classmethod
    async def update_status(cls, event_id: int, score: int):
        new_status = cls.HIGH_SCORE if score >= 3 else cls.LOW_SCORE
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"http://{LP_URL}:{LP_PORT}/events/{event_id}"
                f"/status?status={new_status}"
            )

    @staticmethod
    async def insert_into_score(
            event_id: int,
            score: int
    ):
        session = async_session_maker()
        new_score = ScoreModel(event_id=event_id, score=score)
        session.add(new_score)
        await session.commit()
        await session.refresh(new_score)
        await session.close()
        return new_score.id

    @staticmethod
    async def delete_from_score(
            row_id
    ):
        session = async_session_maker()
        result = await session.execute(
            select(ScoreModel)
            .where(ScoreModel.id == row_id)
        )
        score_row = result.scalar_one()
        await session.delete(score_row)
        await session.commit()
        await session.close()


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
        # return [
        #     parser.isoparse(event["deadline"]) > datetime.now(timezone.utc)
        #     for event in events
        # ]
