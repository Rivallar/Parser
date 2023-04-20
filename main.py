from fastapi import FastAPI
from fastapi_pagination import add_pagination
import uvicorn

from routes.lamoda_routes import lamoda_router
from config import settings

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend


from redis import asyncio as aioredis

app = FastAPI()

app.include_router(lamoda_router)
add_pagination(app)


@app.on_event('startup')
async def startup():
    redis = aioredis.from_url(settings.REDIS, encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")


# @app.on_event('startup')
# def start_consumer():
#     #sleep(15)
#     print('Consumer starting')
#     test_consumer()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)