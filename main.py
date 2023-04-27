from fastapi import FastAPI
from fastapi_pagination import add_pagination
import uvicorn

from config import settings
from routes.lamoda_routes import lamoda_router
from routes.twitch_routes import twitch_router
from scripts.celery_tasks import lamoda_producer, lamoda_consumer, all_twitch_games, stop_all_active_celery_tasks

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from redis import asyncio as aioredis
from time import sleep


app = FastAPI()

app.include_router(lamoda_router)
app.include_router(twitch_router)
add_pagination(app)


@app.on_event('startup')
async def startup():
    redis = aioredis.from_url(settings.REDIS, encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    sleep(30)
    lamoda_consumer.delay()
    lamoda_producer.delay()
    all_twitch_games.delay()


@app.on_event('shutdown')
async def stop_app():
    stop_all_active_celery_tasks()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)