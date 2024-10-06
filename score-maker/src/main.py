import asyncio
import aioredis
from fastapi import FastAPI
from .routers import router_events
from .consumer import consume
from .producer import router_producer
from .config import REDIS_HOST, REDIS_PORT

consumer_task = None
redis = None

app = FastAPI()
app.include_router(router_events)
app.include_router(router_producer)


@app.on_event("startup")
async def startup_event():
    global consumer_task
    global redis
    consumer_task = asyncio.create_task(consume())
    redis = await aioredis.from_url(f"redis://localhost:{REDIS_PORT}")


@app.on_event("shutdown")
async def shutdown_event():
    global consumer_task
    global redis
    if consumer_task:
        consumer_task.cancel()  # Отменяем задачу консюмера
        try:
            await consumer_task  # Ждем завершения задачи
        except asyncio.CancelledError:
            print("Consumer task shutdown successfully")
    if redis:
        await redis.close()