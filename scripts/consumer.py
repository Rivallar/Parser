from datetime import datetime
import logging

from kafka import KafkaConsumer
from json import loads

from config import settings
from database import CatalogDatabase, ItemsDatabase


logging.basicConfig(level=logging.FATAL, filename='consume.log', filemode='a')


def main():
    konsumer = KafkaConsumer(settings.KAFKA_LAMODA_TOPIC,
                             bootstrap_servers=[settings.KAFKA_BROKER],
                             # auto_offset_reset='earliest',
                             enable_auto_commit=True,
                             # group_id='my-group',
                             value_deserializer=lambda x: loads(x.decode('utf-8'))
                             )
    logging.fatal(f'{datetime.now().strftime("%d.%m %H-%M-%S")}:Consumer started')
    buffer = []     # keeps files before saving in DB
    for message in konsumer:

        #   Update catalog tree section
        if message.headers and message.headers[0][1].decode('utf-8') == 'catalog':
            catalog_list = message.value
            if catalog_list:
                db = CatalogDatabase()
                db.drop_collection()
                db.save(catalog_list)
                logging.fatal(f'{datetime.now().strftime("%d.%m %H-%M-%S")}:Updating catalog')

        #   filling buffer with documents of same category
        elif message.headers and message.headers[0][0] == 'catalog_url':
            item = message.value
            item['category_url'] = message.headers[0][1].decode('utf-8')
            item['creation_time'] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            #print(item)
            buffer.append(item)

        #   Saving items to db
        elif message.headers and message.headers[0][0] == 'finished':
            category_url = message.headers[0][1].decode('utf-8')
            db = ItemsDatabase()
            db.delete(many=True, category_url=category_url)
            if buffer:
                db.save(buffer)
            buffer = []
            logging.fatal(f'{datetime.now().strftime("%d.%m %H-%M-%S")}:Category updated:{category_url}')

        #   Clear buffer before starting to collect documents of new category
        elif message.headers and message.headers[0][0] == 'starting':
            buffer = []
            logging.fatal(f'{datetime.now().strftime("%d.%m %H-%M-%S")}:Starting new category:{message.headers[0][1].decode("utf-8")}')


if __name__ == "__main__":
    main()
