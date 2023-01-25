import logging

import uvicorn
from loguru import logger as log

from reviewer.app import init_config

if __name__ == '__main__':
    try:
        uvicorn.run("reviewer.app:app",
                    host=init_config.SERVER_ADDRESS,
                    port=init_config.SERVER_PORT,
                    workers=3,
                    reload=False,
                    log_level=logging.getLevelName(init_config.LOG_LEVEL))

    except Exception as ex:
        log.exception(ex)
