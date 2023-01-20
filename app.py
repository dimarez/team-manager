from review_manager.app import main as TM
import review_manager.mattermost as mm
from loguru import logger as log

if __name__ == '__main__':
    try:
        TM()
        #mm.main()
    except Exception as ex:
        log.exception(ex)
