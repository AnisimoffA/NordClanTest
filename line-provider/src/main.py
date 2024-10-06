import asyncio
from fastapi import FastAPI
from .routers import router_events
from .consumer import consume
from .producer import router_producer


consumer_task = None

app = FastAPI()
app.include_router(router_events)
app.include_router(router_producer)


@app.on_event("startup")
async def startup_event():
    global consumer_task
    consumer_task = asyncio.create_task(consume())
    print("конюсмер успешно подключился")


@app.on_event("shutdown")
async def shutdown_event():
    global consumer_task
    if consumer_task:
        consumer_task.cancel()  # Отменяем задачу консюмера
        try:
            await consumer_task  # Ждем завершения задачи
        except asyncio.CancelledError:
            print("Consumer task shutdown successfully")
