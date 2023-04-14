from pymongo import MongoClient
from pymongo import mongo_client, ASCENDING
from config import settings

# client = mongo_client.MongoClient(settings.DATABASE_URL)
# print('🚀 Connected to MongoDB...')
#
# db = client[settings.MONGO_INITDB_DATABASE]
# Links = db.catalog_urls
# Items = db.items
# Note.create_index([("title", ASCENDING)], unique=True)


def get_database(collection):
    db1 = Database(collection)
    yield db1

    # client1 = MongoClient(settings.DATABASE_URL, 27017)
    # database = client1[settings.MONGO_INITDB_DATABASE]
    #return Database(collection)


class CatalogDatabase:
    def __init__(self):
        self.client = MongoClient(settings.DATABASE_URL, 27017)
        self.database = self.client[settings.MONGO_INITDB_DATABASE]
        self.collection = self.database['catalog_urls']

    def get_all(self):
        result = self.collection.find()
        return result

    def get(self, **conditions):
        result = self.collection.find_one(conditions)
        return result

    def filter(self, limit=None, **conditions):
        result = self.collection.find(conditions)
        if limit:
            result = result[:limit]
        return result

    def save(self, data):
        if isinstance(data, list):
            #dicts = [item.dict() for item in data]
            self.collection.insert_many(data)
        else:
            self.collection.insert_one(data)
        return

    def delete(self, many=False, **conditions):
        if many:
            self.collection.delete_many(conditions)
        else:
            self.collection.delete_one(conditions)

    def drop_collection(self):
        self.collection.drop()


class ItemsDatabase(CatalogDatabase):
    def __init__(self):
        self.client = MongoClient(settings.DATABASE_URL, 27017)
        self.database = self.client[settings.MONGO_INITDB_DATABASE]
        self.collection = self.database['items']