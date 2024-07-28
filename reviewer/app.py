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
log.add(sys.stderr, level=logging.getLevelName(init_config.LOG_LEVEL))
log.info(f"Уровень логирования выставлен на {init_config.LOG_LEVEL}")

if init_config:
    if init_config.SENTRY_DSN:
        import sentry_sdk

        sentry_sdk.init(
            dsn=init_config.SENTRY_DSN,
            traces_sample_rate=init_config.SENTRY_TRACES_SAMPLE_RATE,
        )
    bot = Bot(init_config)
    git = Git(init_config)
    team = Team(git=git)

    if not team:
        log.error("Ошибка инициализации базового класса")
        sys.exit()

from .views import api_router

app = FastAPI()


@app.on_event("startup")
@repeat_every(seconds=init_config.TEAM_CONFIG_UPDATE_INTERVAL, logger=log, wait_first=True)
def periodic():
    team.update_config()


@app.on_event("startup")
@repeat_every(seconds=init_config.MM_BOT_MSG_INTERVAL, logger=log, wait_first=True)
def read_q():
    log.debug(f"Читаем очередь. Интервал {init_config.MM_BOT_MSG_INTERVAL}")
    items = [msg_queue.get() for _ in range(msg_queue.qsize())]
    for queue_mr_result in items:
        if queue_mr_result:
            log.debug(queue_mr_result)
            msg = bot.send_mr_notice_message(queue_mr_result)
            if queue_mr_result.review_channel:
                bot.send_group_message(queue_mr_result)
            if not len(msg):
                msg_error_queue.put(queue_mr_result)
                msg_queue.put(queue_mr_result)
                log.error(f"Ошибка ивента отправки в чат. Item отправлен в очередь с ошибками {queue_mr_result}")



app.include_router(api_router)
