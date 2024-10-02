from dotenv import load_dotenv
import os
from sqlalchemy import MetaData
import asyncio


loop = asyncio.get_event_loop()
load_dotenv()

# для основной бд
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

KAFKA_TOPIC_SCORE_MAKER = os.getenv('KAFKA_TOPIC_SCORE_MAKER')
KAFKA_TOPIC_LINE_PROVIDER = os.getenv('KAFKA_TOPIC_LINE_PROVIDER')
KAFKA_CONSUMER_GROUP = os.getenv('KAFKA_CONSUMER_GROUP')
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')

LP_URL = os.getenv('LP_URL')
LP_PORT = os.getenv('LP_PORT')

metadata = MetaData()
