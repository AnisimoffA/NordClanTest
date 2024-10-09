import json
from aiokafka import AIOKafkaConsumer
from .schemas import EventStatus
from .routers import update_event_status
from .utils import KafkaMethods
from .config import (KAFKA_BOOTSTRAP_SERVERS,
                     KAFKA_TOPIC_LINE_PROVIDER,
                     KAFKA_CONSUMER_GROUP)


async def consume():
    consumer = AIOKafkaConsumer(KAFKA_TOPIC_LINE_PROVIDER,
                                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                                group_id=KAFKA_CONSUMER_GROUP)
    await consumer.start()
    try:
        async for msg in consumer:
            message = json.loads(msg.value.decode('utf-8'))
            event = message['event']
            status = message['status']

            if event == "score_insert_into_db":
                if status == 'success':
                    try:
                        event_id = message['data']['event_id']
                        event_status = EventStatus.HIGH_SCORE \
                            if message['data']['event_score'] >= 3 \
                            else EventStatus.LOW_SCORE
                        await update_event_status(event_id, event_status)

                    except Exception:
                        row_id = message['data']['row_id']
                        await (KafkaMethods.
                               send_score_update_error_message(row_id))
    finally:
        await consumer.stop()
