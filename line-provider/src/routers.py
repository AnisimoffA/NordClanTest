from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from .utils import EventMethods
from .schemas import Event, EventStatus, EventCreate
from .database import get_async_session, async_session_maker
from .models import Event
from .producer import send


router_events = APIRouter()


@router_events.get("/events")
async def get_events(AsyncSession = Depends(get_async_session)):
    result = await AsyncSession.execute(select(Event))
    events = result.scalars().all()
    return events


@router_events.post("/events")
async def create_event(
        event: EventCreate,
        AsyncSession = Depends(get_async_session)
):
    deadline = EventMethods.to_utc_time(event.deadline)
    new_event = Event(title=event.title, deadline=deadline)
    AsyncSession.add(new_event)

    try:
        await AsyncSession.commit()
        await AsyncSession.refresh(new_event)
    except IntegrityError:
        await AsyncSession.rollback()
        raise HTTPException(
            status_code=400,
            detail="Ошибка при добавлении события"
        )
    return new_event


@router_events.get("/events/{event_id}")
async def get_event(event_id: int, AsyncSession = Depends(get_async_session)):
    result = await AsyncSession.execute(
        select(Event).
        where(Event.id == event_id)
    )
    event = result.scalars().first()

    if event is None:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    return event


@router_events.post("/events/{event_id}/status")
async def update_event_status(event_id: int, status: EventStatus):
    session = async_session_maker()
    result = await session.execute(select(Event).where(Event.id == event_id))
    event = result.scalars().first()
    if event:
        event.score_status = status
        await session.commit()
        await session.close()
        return {"status": "Статус обновлено"}
    return {"error": "Событие не найдено"}


@router_events.get("/kafka-test")
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
