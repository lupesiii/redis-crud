from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import redis
import os

load_dotenv()


def connectionMongo():
    url = os.getenv("MONGODB_URI")
    mongo_client = MongoClient(url, server_api=ServerApi("1"))

    try:
        mongo_client.mercado_livre.command("ping")
    except Exception as e:
        print(e)
    return mongo_client.mercado_livre


def connectionRedis():
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST") or "",
        port=15324,
        decode_responses=True,
        username="default",
        password=os.getenv("REDIS_PASSWORD"),
    )

    try:
        pong = redis_client.ping()
        if not pong:
            raise Exception("Redis não connectado")
    except Exception as e:
        print(e)
    return redis_client


dbMongo = connectionMongo()
dbRedis = connectionRedis()
