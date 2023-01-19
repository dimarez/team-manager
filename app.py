from review_manager.app import main as TM
from loguru import logger as log

if __name__ == '__main__':
    try:
        TM()
    except Exception as ex:
        log.exception(ex)


        