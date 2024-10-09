from aiokafka import AIOKafkaProducer
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from sqlalchemy import select
from .models import OutboxMessageModel
from .database import async_session_maker
from .config import (KAFKA_BOOTSTRAP_SERVERS,
                     KAFKA_TOPIC_SCORE_MAKER)


router_producer = APIRouter(
    prefix="/kafka_producer",
    tags=["Producer"]
)


async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        return session


@router_producer.post('/create_message')
async def send_events_to_kafka():
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    await producer.start()
    try:
        async with await get_session() as session:
            result = await session.execute(
                select(OutboxMessageModel).
                where(OutboxMessageModel.status == 'in process')
            )
            events = result.scalars().all()
            for event in events:
                json_data = event.data.encode('utf-8')
                await producer.send_and_wait(
                    topic=KAFKA_TOPIC_SCORE_MAKER,
                    value=json_data
                )
                event.status = 'successfully sent'
                event.processed_on = datetime.now(timezone.utc)
                await session.commit()
    finally:
        await producer.stop()
