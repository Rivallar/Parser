from typing import Optional

from pydantic import BaseModel
import pydantic
from bson.objectid import ObjectId


pydantic.json.ENCODERS_BY_TYPE[ObjectId]=str


class CatalogLink(BaseModel):
    buyer_type: str
    category: str
    subcategory: str
    url_string: str


class Item(BaseModel):
    category_url: str
    item_url: str
    price: str
    brand_name: str
    description: str
    image_url: str
    characteristics: dict
    creation_time: Optional[str]
