from time import sleep

import requests
from bs4 import BeautifulSoup
from kafka import KafkaProducer
from json import dumps
import logging

from slugify import slugify

from models import CatalogLink
from config import settings


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
                        links.append(new_link.dict())

    return links


def last_category_url():
    try:
        with open('parse.log', 'r') as log:
            lines = log.readlines()[::-1]
            lines = lines[:30]
            for line in lines:
                if 'WARNING' in line:
                    url_with_page = line.split(':', 3)[-1].strip()
                    url = url_with_page.split('?')[0]
                    return url
    except FileNotFoundError:
        return None


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


def parse_subcategory(url, producer, page=1):

    completed = False
    headers = [('catalog_url', url.encode('utf-8'))]

    while not completed:
        curr_page = f'{url}?page={page}'
        logging.warning(f'{page}:{curr_page}')
        for href in get_hrefs_from_page(curr_page):
            if href == "No more items":
                producer.send('testtopic', {'end_of_cat': 'finished'}, headers=[('finished', url.encode('utf-8'))])
                completed = True
                logging.info('No more items to parse. Task is complete.')
                break

            parsed_item = parse_single_item(href)
            print(parsed_item)
            producer.send('testtopic', parsed_item, headers=headers)

        page += 1


def main():
    producer = KafkaProducer(bootstrap_servers=[settings.KAFKA_BROKER],
                             value_serializer=lambda x: dumps(x).encode('utf-8'))

    catalog = build_catalog_tree()

    headers = [('type', b"catalog")]
    if catalog:
        producer.send('testtopic', catalog, headers=headers)

    catalog_urls = [item['url_string'] for item in catalog]
    last_url = last_category_url()
    print(last_url)
    if last_url:
        try:
            start_ind = catalog_urls.index(last_url)
            catalog_urls = catalog_urls[start_ind:]
        except ValueError:
            pass

    for url in catalog_urls:
        producer.send('testtopic', {'new_cat': 'starting'}, headers=[('starting', url.encode('utf-8'))])
        parse_subcategory(url, producer)


if __name__ == "__main__":
    main()
