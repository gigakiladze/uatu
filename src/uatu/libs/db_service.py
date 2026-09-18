
from functools import cache

from pymongo import MongoClient
from pymongo.database import Database

from uatu.libs.config import settings


@cache
def get_client() -> MongoClient:

    return MongoClient(settings.mongo_uri, 
                       maxPoolSize=settings.mongo_max_pool_size,
                       minPoolSize=settings.mongo_min_pool_size,
                       connectTimeoutMS=settings.mongo_connect_timeout_ms,
                       appname=settings.mongo_app_name,
                       tz_aware=settings.mongo_tz_aware)

@cache
def get_db() -> Database:

    return get_client()[settings.mongo_db_name]

def ping() -> bool:

    get_client().admin.command("ping")
    return True