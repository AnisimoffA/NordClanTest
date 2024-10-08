from asyncio import sleep
import json
from fastapi import APIRouter, Request
from .schemas import Score, KafkaEvent
from datetime import datetime, timezone
import time
from .utils import (EventUsefulMethods,
                    EventRemoteMethods,
                    ScoreDBMethods,
                    ScoreMethods,
                    EventValidator)
from .producer import send


router_events = APIRouter(tags=["Score-maker"])


@router_events.get("/events")
async def get_events(request: Request):
    redis = request.app.state.redis
    events = redis.get("valid_events")

    if events is None:
        events = await EventRemoteMethods.get_all_events()
        valid_events = [
            event for event in events
            if EventUsefulMethods.to_utc_time(event["deadline"])
               > datetime.now(timezone.utc)
        ]
        redis.set("valid_events", json.dumps(valid_events), ex=1800)
    else:
        events = json.loads(events)
    return events


@router_events.get("/scores")
async def get_scores():
    scores = await ScoreDBMethods.select_all_from_score()
    events = await EventRemoteMethods.get_all_events()
    actual_events = ScoreMethods.check_actuality(events)
    return [
        {
            "id": score.id,
            "score_id": score.event_id,
            "changeable": score.id in actual_events
        }
        for score in scores
    ]


@router_events.post("/set-score")
async def set_score(score: Score):
    event = await EventRemoteMethods.get_event_by_id(score.event_id)
    deadline = EventUsefulMethods.to_utc_time(event["deadline"])

    EventValidator.validate_deadline(deadline)

    try:
        row_id = await ScoreDBMethods.insert_into_score(
            score.event_id,
            score.score
        )
        message = KafkaEvent(
            data={
                "event_id": score.event_id,
                "event_score": score.score,
                "row_id": row_id
            },
            event="score_insert_into_db",
            status="success"
        )
        await send(message.dict())
        return {"score_id": score.event_id, "status": "Создано"}
    except Exception as e:
        message = KafkaEvent(
            data=None,
            event="score_insert_into_db",
            status="error"
        )
        await send(message.dict())
        return HTTPException(status_code=400, detail=e)


@router_events.get("/kafka-test")
async def kafka_test():
    try:
        message = KafkaEvent(
            data=None,
            event="test",
            status="success"
        )
        await send(message.dict())
        return {"status": "success", "info": "все успешно отправлено"}
    except Exception as e:
        return {"status": "error", "error": str(e)}