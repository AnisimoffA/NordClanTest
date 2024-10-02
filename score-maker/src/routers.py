import json
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from fastapi import APIRouter, HTTPException, Depends
from .schemas import Score
from datetime import datetime, timezone
from .models import ScoreModel
from .database import get_async_session
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from .utils import EventMethods, ScoreMethods
from dateutil import parser
from .config import (KAFKA_BOOTSTRAP_SERVERS,
                     KAFKA_TOPIC_SCORE_MAKER,
                     KAFKA_TOPIC_LINE_PROVIDER,
                     KAFKA_CONSUMER_GROUP)


router = APIRouter()


@router.post('/create_message')
async def send(message):
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    await producer.start()
    try:
        value_json = json.dumps(message).encode('utf-8')
        await producer.send_and_wait(
            topic=KAFKA_TOPIC_LINE_PROVIDER,
            value=value_json
        )
    finally:
        await producer.stop()


async def consume():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC_SCORE_MAKER,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=KAFKA_CONSUMER_GROUP,

    )
    await consumer.start()
    try:
        async for msg in consumer:
            message = json.loads(msg.value.decode('utf-8'))
            event = message['event']
            status = message['status']

            if event == "score_update":
                if status == "error":
                    row_id = message['data']['row_id']
                    await EventMethods.delete_from_score(row_id)
    finally:
        await consumer.stop()


@router.get("/events")
async def get_events():
    events = await EventMethods.get_all_events()
    return [
        event
        for event
        in events
        if EventMethods.to_utc_time(event["deadline"]) > datetime.now(timezone.utc)
        ]


@router.get("/scores")
async def get_scores(
        session: AsyncSession = Depends(get_async_session)
):
    query = select(ScoreModel)
    result = await session.execute(query)
    scores = result.scalars().all()
    events = await EventMethods.get_all_events()
    actual_events = ScoreMethods.check_actuality(events)

    return [
        {
            "id": score.id,
            "score_id": score.event_id,
            "changeable": score.id in actual_events
        }
        for score in scores
    ]


@router.post("/set-score")
async def set_score(
        score: Score,
):
    event = await EventMethods.get_event_by_id(score.event_id)
    deadline = EventMethods.to_utc_time(event["deadline"])

    if deadline < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Событие нельзя оценить")

    try:
        row_id = await EventMethods.insert_into_score(
            score.event_id,
            score.score
        )
        await send(message={
            "data": {
                "event_id": score.event_id,
                "event_score": score.score,
                "row_id": row_id},
            "event": "score_insert_into_db",
            "status": "success"
        })
        return {"score_id": score.event_id, "status": "Создано"}
    except Exception as e:
        await send(message={
            "data": None,
            "event": "score_insert_into_db",
            "status": "error"
        })
        return HTTPException(status_code=400, detail=e)



@router.get("/kafka-test")
async def kafka_test():
    try:
        await send(message={
            "data": None,
            "event": "test",
            "status": "success"
        })
        return {"status": "success", "info": "все успешно отправлено"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
