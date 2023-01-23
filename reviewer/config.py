import os
import sys
from enum import Enum

from loguru import logger as log
from pydantic import BaseModel, ValidationError, root_validator


class LogLevel(str, Enum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class InitConfig(BaseModel):
    GITLAB_URL: str
    GITLAB_TOKEN: str
    MM_TOKEN: str
    MM_URL: str
    MM_PORT: int = 443
    TEAM_CONFIG_PROJECT: str
    TEAM_CONFIG_FILE: str = "team-config.yaml"
    LOG_LEVEL: LogLevel = LogLevel.INFO
    SERVER_TOKEN: str
    SERVER_ADDRESS: str = "0.0.0.0"
    SERVER_PORT: int = 8080
    TEAM_CONFIG_UPDATE_INTERVAL: int = 60

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
