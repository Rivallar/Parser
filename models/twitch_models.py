from typing import Optional

from pydantic import BaseModel
import pydantic
from bson.objectid import ObjectId


pydantic.json.ENCODERS_BY_TYPE[ObjectId]=str


class Game(BaseModel):
    name: str
    box_art_url: Optional[str]


class Stream(BaseModel):
    user_name: str
    game_name: str
    title: Optional[str]
    viewer_count: int
    started_at: str
    language: str
    is_mature: bool


class SearchResult(BaseModel):
    id: str
    name: str


class Channel(BaseModel):
    broadcaster_language: str
    display_name: str
    game_name: str
    tags: Optional[list]
    title: Optional[str]
    started_at: str


class TwitchUser(BaseModel):
    id: str
    display_name: str
    broadcaster_type: Optional[str]
    description: Optional[str]
    profile_image_url: Optional[str]
    offline_image_url: Optional[str]
    view_count: int
    created_at: str
