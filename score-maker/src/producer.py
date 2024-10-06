import json
from aiokafka import AIOKafkaProducer
from fastapi import APIRouter
# from .schemas import KafkaEvent
from .config import (KAFKA_BOOTSTRAP_SERVERS,
                     KAFKA_TOPIC_LINE_PROVIDER)


router_producer = APIRouter(
    prefix="/kafka_producer",
    tags=["Producer"]
)


@router_producer.post('/create_message')
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
