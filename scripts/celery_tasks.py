import asyncio

from celery import Celery
from time import sleep

from config import settings
from scripts.producer import main as parse_lamoda
from scripts.consumer import main as consume_lamoda
from scripts.twitch_scripts import get_token, get_all_games

tasks_app = Celery(
    'tasks',
    broker=settings.CELERY_BROKER,
    backend=settings.CELERY_BACKEND
)


def stop_all_active_celery_tasks():
    print('Stopping celery tasks')
    inspect = tasks_app.control.inspect
    revoke = tasks_app.control.revoke
    for worker_name, tasks in inspect().active().items():
        for task in tasks:
            revoke(task['id'], terminate=True)


@tasks_app.task
def lamoda_consumer():
    consume_lamoda()


@tasks_app.task
def lamoda_producer():
    while True:
        coro = parse_lamoda()
        asyncio.run(coro)


@tasks_app.task
def all_twitch_games():
    while True:
        sleep(60)
        token = get_token()
        get_all_games(token)
