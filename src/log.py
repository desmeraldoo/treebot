import datetime
import logging
import os
from typing import Final

from src.settings import LOGGER_NAME

LOG_FILE_INFO: Final[str] = "logs/reg-{}.log"
LOG_FILE_DEBUG: Final[str] = "logs/reg-debug-{}.log"
LOG_FORMAT_FILE: Final[str] = "%(asctime)s [%(name)s] [%(levelname)s] %(message)s"
LOG_FORMAT_STREAM: Final[str] = "%(asctime)s [%(levelname)s] %(message)s"


def init_logging():
    if not os.path.isdir("logs"):
        os.mkdir("logs")

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.NOTSET)

    log_formatter_file = logging.Formatter(LOG_FORMAT_FILE)
    log_formatter_stream = logging.Formatter(LOG_FORMAT_STREAM)
    today = datetime.date.today().strftime("%m-%d-%y")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_formatter_stream)
    stream_handler.setLevel(logging.INFO)
    logger.addHandler(stream_handler)

    file_handler_info = logging.FileHandler(LOG_FILE_INFO.format(today), mode="a")
    file_handler_info.setFormatter(log_formatter_file)
    file_handler_info.setLevel(logging.INFO)
    logger.addHandler(file_handler_info)

    file_handler_debug = logging.FileHandler(LOG_FILE_DEBUG.format(today), mode="a")
    file_handler_debug.setFormatter(log_formatter_file)
    file_handler_debug.setLevel(logging.DEBUG)
    logger.addHandler(file_handler_debug)

    logging.raiseExceptions = False
    logging.getLogger("nextcord").setLevel(logging.INFO)
