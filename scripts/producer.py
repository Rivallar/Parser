import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from json import dumps
from kafka import KafkaProducer
import logging
import requests
import redis
from slugify import slugify
from time import sleep

from models.lamoda_models import CatalogLink
from config import settings


logging.basicConfig(level=logging.FATAL, filename='produce.log', filemode='a')

r = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)


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
                        links.append(new_link.dict())

    return links


def get_hrefs_from_page(url):

    """Returns items detail urls from a page with list of items."""

    base_url = 'https://www.lamoda.by'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    items = soup.find("div", class_="grid__catalog")
    if not items:
        return
    else:
        hrefs = [f"{base_url}{href.get('href')}" for href in items.find_all("a")]
        return hrefs


async def parse_single_item(session, url):

    """Parses a single detail page of an item and returns a dict with some information."""

    # print(f'Parsing {url}')
    async with session.get(url, ssl=False) as req:
        response = await req.text()

        soup = BeautifulSoup(response, 'lxml')
        try:
            price = soup.find_all("span", class_="x-premium-product-prices__price")[
                -1].text.strip()  # last price with discount
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

        try:
            image_url = f'https:{soup.find("img").get("src")}'
        except AttributeError:
            image_url = 'attribute is missing'

        params = soup.find_all("span", class_='x-premium-product-description-attribute__name')
        values = soup.find_all("span", class_='x-premium-product-description-attribute__value')
        parameters = {}
        for p, v in zip(params, values):
            parameters[p.text] = v.text

        result = {'item_url': url, 'price': price, 'brand_name': brand_name, 'description': descr,
                  'image_url': image_url, 'characteristics': parameters}

        return result


async def parse_subcategory(url, producer, page=1):

    """Loops through a whole category and parses all items. Sends Each item to kafka."""



    completed = False
    headers = [('catalog_url', url.encode('utf-8'))]        # headers are used by consumer to discern actions

    r.set('last_cat_url', url)

    while not completed:
        curr_page = f'{url}?page={page}'

        #r.set('last_cat_page', page)
        if page % 50 == 0:
            logging.fatal('Gonna sleep for a while')
            sleep(300)

        logging.fatal(f'{datetime.now().strftime("%d.%m %H-%M-%S")}:{page}:{curr_page}')
        hrefs = get_hrefs_from_page(curr_page)

        if not hrefs:
            producer.send(settings.KAFKA_LAMODA_TOPIC, {'end_of_cat': 'finished'},
                          headers=[('finished', url.encode('utf-8'))])
            completed = True
            logging.fatal(f'{datetime.now().strftime("%d.%m %H-%M-%S")}:No more items to parse. Task is complete.')
            break

        async with aiohttp.ClientSession() as session:
            tasks = []
            for href in hrefs:
                tasks.append(asyncio.ensure_future(parse_single_item(session, href)))
            all_items = await asyncio.gather(*tasks)
            for item in all_items:
                producer.send(settings.KAFKA_LAMODA_TOPIC, item, headers=headers)
        page += 1


async def main():

    """Launches parsing task. Refreshes catalog tree, then defines from log where it stopped and starts parsing from
    that point."""

    producer = KafkaProducer(bootstrap_servers=[settings.KAFKA_BROKER],
                             value_serializer=lambda x: dumps(x).encode('utf-8'))

    # Updating catalog tree
    catalog = build_catalog_tree()
    headers = [('type', b"catalog")]        # headers are used by consumer to discern actions
    if catalog:
        producer.send(settings.KAFKA_LAMODA_TOPIC, catalog, headers=headers)

    # Defining from which category to start parsing
    catalog_urls = [item['url_string'] for item in catalog]
    last_url = r.get('last_cat_url').decode()
    if last_url:

        try:
            start_ind = catalog_urls.index(last_url)
            catalog_urls = catalog_urls[start_ind:]
        except ValueError:
            pass

    # parsing categories from catalog_urls
    for url in catalog_urls:
        producer.send(settings.KAFKA_LAMODA_TOPIC, {'new_cat': 'starting'}, headers=[('starting', url.encode('utf-8'))])
        await parse_subcategory(url, producer)
        if url == catalog_urls[-1]:
            r.set('last_cat_url', '')


if __name__ == "__main__":
    asyncio.run(main())
