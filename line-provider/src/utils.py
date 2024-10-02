import aiohttp
from fastapi.exceptions import HTTPException
from dateutil import parser
from datetime import datetime, timezone
from sqlalchemy import select
from .database import async_session_maker
from .models import Event


class EventMethods:
    @staticmethod
    def to_utc_time(current_deadline):
        correct_deadline = current_deadline.astimezone(timezone.utc).replace(tzinfo=None)
        return correct_deadline