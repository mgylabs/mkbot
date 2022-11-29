import glob
import logging
import os
import time

from mgylabs.utils.config import USER_DATA_PATH, is_development_mode

if is_development_mode():
    LOG_LEVEL = logging.INFO
else:
    LOG_LEVEL = logging.WARNING


class LogPath:
    LOG_FILE_PATH = f"{USER_DATA_PATH}\\logs\\mkbot-{int(time.time())}.log"

    @classmethod
    def get(cls):
        return cls.LOG_FILE_PATH

    @classmethod
    def update(cls):
        cls.LOG_FILE_PATH = f"{USER_DATA_PATH}\\logs\\mkbot-{int(time.time())}.log"


def delete_old_logs(log, max_count=20):
    p = f"{USER_DATA_PATH}\\logs\\mkbot-*.log"
    files = list(filter(os.path.isfile, glob.glob(p)))
    files.sort(key=lambda x: os.path.getmtime(x))

    files_len = len(files)

    log.info(f"Find {files_len} log file(s)")

    diff = files_len - max_count

    if diff > 0:
        for f in files[:diff]:
            try:
                log.info(f"Delete {f}")
                os.remove(f)
            except Exception as e:
                log.error(e)


def configure_logger(file_path=LogPath.get(), cleanup=True):
    log = logging.getLogger("mkbot")
    log.propagate = True
    formatter = logging.Formatter(
        "[%(asctime)s.%(msecs)03d] %(name)s (line %(lineno)d): %(levelname)s - %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(LOG_LEVEL)
    stream_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(file_path, mode="w", encoding="utf-8")
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)
    log.addHandler(stream_handler)
    log.addHandler(file_handler)
    log.setLevel(LOG_LEVEL)

    # logger = logging.getLogger("discord")
    # logger.setLevel(logging.DEBUG)
    # logger.addHandler(stream_handler)

    if cleanup:
        delete_old_logs(log)


def get_logger(name):
    log = logging.getLogger(f"mkbot.{name}")
    return log
