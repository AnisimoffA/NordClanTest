import asyncio
from fastapi import FastAPI
from .routers import router_events
from .consumer import consume
from .producer import router_producer


app = FastAPI()
app.include_router(router_events)
app.include_router(router_producer)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(consume())
