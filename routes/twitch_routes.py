from fastapi import APIRouter, Path, Depends, HTTPException, status
from fastapi_pagination import Page, paginate
from typing import List

from twitch_scripts import read_all_games, get_game_streams, get_game_id, get_token, search_game, search_channels, get_user
from twitch_models import Game, Stream, SearchResult, Channel, TwitchUser

twitch_router = APIRouter()


@twitch_router.get("/twitch/games", response_model=Page[Game])
async def all_games(token=Depends(get_token)):

    """Obtains list of all games"""

    games = read_all_games(token)
    return paginate(games)


@twitch_router.get("/twitch/game_streams", response_model=Page[Stream])
async def game_streams(game_name: str, language: str = None, token=Depends(get_token)):

    """Streams of a game by exact game-name. Can filter by language of a streamer."""

    game_id = get_game_id(game_name, token)
    streams = get_game_streams(game_id, token, language)
    return paginate(streams)


@twitch_router.get("/twitch/search_games", response_model=Page[SearchResult])
async def search_twitch_game(query: str, token=Depends(get_token)):

    """Search games and their id`s by inexact name."""

    result = search_game(token, query)
    return paginate(result)


@twitch_router.get("/twitch/search_channels", response_model=Page[Channel])
async def search_twitch_channel(query: str, token=Depends(get_token)):

    """Search streams with query value in game name or stream name"""

    result = search_channels(token, query)
    return paginate(result)


@twitch_router.get("/twitch/search_user", response_model=TwitchUser)
async def search_twitch_user(user_id: int = None, user_login: str = None, token=Depends(get_token)):

    """Get info of a single user."""

    user = get_user(token, user_id, user_login)[0]
    return user

