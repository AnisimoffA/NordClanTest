from fastapi import APIRouter
from .utils import EventUsefulMethods, EventDBMethods
from .schemas import EventStatus, EventCreate, KafkaEvent
from .producer import send


router_events = APIRouter(tags=["Line-provider"])

@router_events.get("/events")
async def get_events():
    events = await EventDBMethods.select_all_events()
    return events


@router_events.post("/events")
async def create_event(event: EventCreate):
    deadline = EventUsefulMethods.to_utc_time(event.deadline)
    await EventDBMethods.insert_into_event(event, deadline)
    return event


@router_events.get("/events/{event_id}")
async def get_event(event_id: int):
    event = await EventDBMethods.select_event_by_id(event_id)
    return event


@router_events.post("/events/{event_id}/status")
async def update_event_status(event_id: int, status: EventStatus):
    await EventDBMethods.update_event_status(event_id, status)
    return {"status": "Статус обновлено"}


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
