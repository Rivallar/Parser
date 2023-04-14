from fastapi import FastAPI
from fastapi_pagination import add_pagination
import uvicorn
from time import sleep

from lamoda_scripts import parse_subcategory, test_consumer
from routes.lamoda_routes import lamoda_router

app = FastAPI()

app.include_router(lamoda_router)
add_pagination(app)


# @app.on_event('startup')
# async def start_producer():
#     print('Starting producer')
#     await parse_subcategory('https://www.lamoda.by/c/203/shoes-girls/')


# @app.on_event('startup')
# def start_consumer():
#     #sleep(15)
#     print('Consumer starting')
#     test_consumer()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)