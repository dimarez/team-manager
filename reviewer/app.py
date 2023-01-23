import sys

from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from loguru import logger as log

from .config import init_environment
from .teams import Git, Team

init_config = init_environment()

if init_config:
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


app.include_router(api_router)
