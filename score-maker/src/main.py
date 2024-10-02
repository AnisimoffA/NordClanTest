import asyncio
from fastapi import FastAPI
from .routers import router, consume


app = FastAPI()
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(consume())
