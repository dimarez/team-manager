import logging
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
msg_error_queue = Queue()

log.remove()
log.add(sys.stderr, format="{time} {level} {message}", level=logging.getLevelName(init_config.LOG_LEVEL))
log.info(f"Уровень логирования выставлен на {init_config.LOG_LEVEL}")


if init_config:
    bot = Bot(init_config)

    git = Git(init_config)
    team = Team(git=git)
    if not team:
        log.error("Ошибка инициализации базового класса")
        sys.exit()

from .views import api_router

app = FastAPI()


@app.on_event("startup")
@repeat_every(seconds=init_config.MM_BOT_MSG_INTERVAL, logger=log, wait_first=True)
def read_q():
    log.debug(f"Читаем очередь. Интервал {init_config.MM_BOT_MSG_INTERVAL}")
    items = [msg_queue.get() for _ in range(msg_queue.qsize())]
    for qdata in items:
        if qdata:
            msg = bot.send_mr_notice_message(qdata)
            if msg:
                log.info("Отправлено сообщение в чат")
                log.debug(f"Отправлено сообщение в чат -> {msg}")
            else:
                msg_error_queue.put(qdata)
                msg_queue.put(qdata)
                log.error(f"Ошибка эвента отправки в чат. Item отправлен в очередь с ошибками {qdata}")


@app.on_event("startup")
@repeat_every(seconds=init_config.TEAM_CONFIG_UPDATE_INTERVAL, logger=log, wait_first=True)
def periodic():
    team.update_config()


app.include_router(api_router)
