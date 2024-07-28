import os
import sys
from enum import Enum
from typing import Optional

from loguru import logger as log
from pydantic import BaseModel, ValidationError, root_validator, HttpUrl, EmailStr


class LogLevel(str, Enum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class InitConfig(BaseModel):
    GITLAB_URL: HttpUrl
    GITLAB_TOKEN: str
    MM_TOKEN: str
    MM_HOST: str
    MM_PORT: int = 443
    MM_BOT_MSG_INTERVAL: int = 30
    TEAM_CONFIG_PROJECT: str
    TEAM_CONFIG_FILE: str = "team-config.yaml"
    TEAM_CONFIG_BRANCH: str = "master"
    LOG_LEVEL: LogLevel = LogLevel.INFO
    AUTH_TOKEN: Optional[str]
    SERVER_ADDRESS: str = "0.0.0.0"
    SERVER_PORT: int = 8080
    SERVER_WORKERS: int = 3
    TEAM_CONFIG_UPDATE_INTERVAL: int = 60
    SENTRY_DSN: Optional[HttpUrl]
    SENTRY_TRACES_SAMPLE_RATE: float = 1.0
    DEBUG_REVIEWER_ID: Optional[int]
    DEBUG_REVIEWER_EMAIL: Optional[EmailStr]
    DEBUG_REVIEWER_USERNAME: Optional[str]
    DEBUG_MR_SETUP: Optional[bool]

    @root_validator(pre=True)
    def to_uppercase(cls, values: dict):
        upper_val = {}
        for k, v in values.items():
            if str(k).upper() == "LOG_LEVEL":
                v = str(v).upper()
            upper_val[str(k).upper()] = v
        return upper_val


def init_environment() -> InitConfig:
    try:
        init_cfg = InitConfig.parse_obj(os.environ)
        return init_cfg
    except ValidationError as ex:
        log.error(f"Ошибка загрузки ENV-параметров конфигурации -> [{ex}]")
        sys.exit()
