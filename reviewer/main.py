import logging
import sys

import uvicorn
from loguru import logger as log

from reviewer.app import init_config

if __name__ == '__main__':
    try:
        # logger_format = (
        #     "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        #     "<level>{level: <8}</level> | "
        #     "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        #     "- <level>{message}</level>"
        # )
        log.remove()
        log.add(sys.stderr, level=logging.getLevelName(init_config.LOG_LEVEL))
        log.info(f"Уровень логирования выставлен на {init_config.LOG_LEVEL}")

        uvicorn.run("reviewer.app:app",
                    host=init_config.SERVER_ADDRESS,
                    port=init_config.SERVER_PORT,
                    workers=3,
                    reload=False,
                    log_level=logging.getLevelName(init_config.LOG_LEVEL))

    except Exception as ex:
        log.exception(ex)