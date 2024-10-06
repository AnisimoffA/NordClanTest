import json
from aiokafka import AIOKafkaConsumer
from .utils import ScoreDBMethods
from .config import (KAFKA_BOOTSTRAP_SERVERS,
                     KAFKA_TOPIC_SCORE_MAKER,
                     KAFKA_CONSUMER_GROUP)


async def consume():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC_SCORE_MAKER,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=KAFKA_CONSUMER_GROUP,

    )
    await consumer.start()
    try:
        async for msg in consumer:
            message = json.loads(msg.value.decode('utf-8'))
            event = message['event']
            status = message['status']

            if event == "score_update":
                if status == "error":
                    row_id = message['data']['row_id']
                    await ScoreDBMethods.delete_from_score(row_id)
    finally:
        await consumer.stop()
