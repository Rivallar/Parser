import requests
from bs4 import BeautifulSoup
from kafka import KafkaProducer
from json import dumps

from slugify import slugify

from models import CatalogLink
from config import settings


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


def main():
    producer = KafkaProducer(bootstrap_servers=[settings.KAFKA_BROKER],
                             value_serializer=lambda x: dumps(x).encode('utf-8'))

    catalog = build_catalog_tree()
    headers = [('type', b"catalog")]
    if catalog:
        producer.send('testtopic', catalog, headers=headers)


if __name__ == "__main__":
    main()
