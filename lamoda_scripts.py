from datetime import datetime
from time import sleep
import logging

from kafka import KafkaProducer, KafkaConsumer
from json import dumps, loads

from bs4 import BeautifulSoup
import requests

from database import get_database
from models import CatalogLink, Item
from config import settings


from pymongo import MongoClient
from slugify import slugify


logging.basicConfig(level=logging.INFO, filename='parse.log', filemode='a')


def build_catalog_tree():

    """Returns a list of CatalogLink objects"""

    base_url = 'https://www.lamoda.by'
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, 'lxml')

    links = []

    catalog_section = soup.find("div", class_='x-footer-seo-menu-tabs')

    for child in catalog_section.children:
        if child.get("class")[0] == 'x-footer-seo-menu-tab-title':
            if child.text == 'Бренды':
                break

            first_layer_name = slugify(child.text)

        elif child.get("class")[0] == 'x-footer-seo-menu-tab':
            for category in child. children:
                if category.get("class")[0] == 'x-footer-seo-menu-tab-category':
                    if child.text == 'Бренды':
                        break
                    sec_layer_name = slugify(category.text)

                elif category.get("class")[0] == 'x-footer-seo-menu-tab-links':
                    hrefs = category.find_all("a", class_='x-footer-seo-menu-tab-links__item')
                    for href in hrefs[1:]:
                        third_layer_text = slugify(href.text)
                        url = f'{base_url}{href.get("href")}'

                        new_link = CatalogLink(buyer_type=first_layer_name, category=sec_layer_name,
                                               subcategory=third_layer_text, url_string=url)
                        links.append(new_link)

    return links


def save_or_update(q, item, db_repo):
    if not q:
        db_repo.insert_one(item)
    else:
        update_query = {"$set": {field: value for field, value in item.dict().items()}}
        db_repo.update_one(q, update_query)


def update_catalog_tree_to_db():

    """Rebuilds catalog tree in DB"""

    catalog = build_catalog_tree()      # parsing from site
    if catalog:
        repo = get_database().catalog_urls
        repo.drop()
        for item in catalog:
            repo.insert_one(item.dict())


def get_hrefs_from_page(url):
    base_url = 'https://www.lamoda.by'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    items = soup.find("div", class_="grid__catalog")
    if not items:
        yield "No more items"

    else:
        hrefs = [f"{base_url}{href.get('href')}" for href in items.find_all("a")]
        for href in hrefs:
            yield href


def parse_single_item(url):

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    try:
        price = soup.find_all("span", class_="x-premium-product-prices__price")[-1].text.strip()            # last price with discount
    except IndexError:
        price = 'Нет в наличии'

    try:
        brand_name = soup.find("span", class_="x-premium-product-title__brand-name").text.strip()
    except AttributeError:
        brand_name = 'attribute is missing'

    try:
        descr = soup.find("div", class_="x-premium-product-title__model-name").text.strip()
    except AttributeError:
        descr = 'attribute is missing'

    params = soup.find_all("span", class_='x-premium-product-description-attribute__name')
    values = soup.find_all("span", class_='x-premium-product-description-attribute__value')

    try:
        image_url = f'https:{soup.find("img").get("src")}'
    except AttributeError:
        image_url = 'attribute is missing'

    parameters = {}
    for p, v in zip(params, values):
        parameters[p.text] = v.text

    result = {'item_url': url, 'price': price, 'brand_name': brand_name, 'description': descr,
              'image_url': image_url, 'characteristics': parameters}
    return result


def parse_subcategory(url, page=1):

    producer = KafkaProducer(bootstrap_servers=['broker:29092'],
                             value_serializer=lambda x: dumps(x).encode('utf-8'))


    completed = False

    client = MongoClient('localhost', 27017)
    collection = client.parserDB.items

    while not completed:
        curr_page = f'{url}?page={page}'
        logging.info(f'Parsing page {page}. Url is: {curr_page}')
        for href in get_hrefs_from_page(curr_page):
            if href == "No more items":
                completed = True
                logging.info('No more items to parse. Task is complete.')
                break

            parsed_item = parse_single_item(href)
            print(parsed_item)
            producer.send('testtopic', parsed_item)
            #save_to_db(parsed_item, collection, url)
            sleep(2)

        page += 1


def save_to_db(parsed_item, collection, cat_url):
    db_item = Item(item_url=parsed_item['item_url'], price=parsed_item['price'], brand_name=parsed_item['brand_name'],
                   description=parsed_item['description'], image_url=parsed_item['image_url'],
                   characteristics=parsed_item['characteristics'], category_url=cat_url)

    q = collection.find_one({'item_url': db_item.item_url})
    if not q:
        db_item.creation_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        collection.insert_one(dict(db_item))
    else:
        update_query = {"$set": {field: value for field, value in dict(db_item).items()}}
        collection.update_one(q, update_query)


def test_consumer():

    print('Consumer starting')
    konsumer = KafkaConsumer('testtopic',
                             bootstrap_servers=[settings.KAFKA_BROKER],
                             #auto_offset_reset='earliest',
                             enable_auto_commit=True,
                             #group_id='my-group',
                             value_deserializer=lambda x: loads(x.decode('utf-8'))
                             )
    for message in konsumer:
        # if message.headers[0][1].decode('utf-8') == 'catalog':
        #     catalog_list = message.value
        #     if catalog_list:
        #         repo = get_database().catalog_urls
        #         for item in catalog_list:
        #             repo.insert_one(item)
        print(message.headers[0][1].decode('utf-8'))
