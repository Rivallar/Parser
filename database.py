from pymongo import MongoClient
from pymongo import mongo_client, ASCENDING
from config import settings

client = mongo_client.MongoClient(settings.DATABASE_URL)
print('🚀 Connected to MongoDB...')

db = client[settings.MONGO_INITDB_DATABASE]
Links = db.catalog_urls
Items = db.items
# Note.create_index([("title", ASCENDING)], unique=True)


def get_database():
    client1 = MongoClient('localhost', 27017)
    database = client1.parserDB
    return database
