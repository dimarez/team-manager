import sys
from queue import Queue

from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from loguru import logger as log

from .bot import Bot
from .config import init_environment
from .teams import Git, Team

init_config = init_environment()

msg_queue = Queue()

if init_config:

    bot = Bot(init_config)
    resp = bot._connect()

    # bot.send_private_message('drezn@a-fin.tech', 'Превед! Я бот-доставатель с код-ревью. Тестирую интеграцию с сервисом team-manager. Ты меня видишь?')

    # bot.generate_mr_notice()

    git = Git(init_config)
    team = Team(git=git)
    if not team:
        log.error("Ошибка инициализации базового класса")
        sys.exit()

from .views import api_router

app = FastAPI()


@app.on_event("startup")
@repeat_every(seconds=10, logger=log, wait_first=True)
def read_q():
    log.debug("Читаем очередь")
    qdata = msg_queue.get()
    log.debug(f"данные -> {qdata}")


@app.on_event("startup")
@repeat_every(seconds=init_config.TEAM_CONFIG_UPDATE_INTERVAL, logger=log, wait_first=True)
def periodic():
    team.update_config()


app.include_router(api_router)
