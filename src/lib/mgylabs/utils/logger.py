import glob
import logging
import os
import time

from mgylabs.utils.config import USER_DATA_PATH, is_development_mode

if is_development_mode():
    LOG_LEVEL = logging.INFO
else:
    LOG_LEVEL = logging.INFO


class ColorFormatter(logging.Formatter):
    # ANSI codes are a bit weird to decipher if you're unfamiliar with them, so here's a refresher
    # It starts off with a format like \x1b[XXXm where XXX is a semicolon separated list of commands
    # The important ones here relate to colour.
    # 30-37 are black, red, green, yellow, blue, magenta, cyan and white in that order
    # 40-47 are the same except for the background
    # 90-97 are the same but "bright" foreground
    # 100-107 are the same as the bright ones but for the background.
    # 1 means bold, 2 means dim, 0 means reset, and 4 means underline.

    LEVEL_COLOURS = [
        (logging.DEBUG, "\x1b[40;1m"),
        (logging.INFO, "\x1b[34;1m"),
        (logging.WARNING, "\x1b[33;1m"),
        (logging.ERROR, "\x1b[31;1m"),
        (logging.CRITICAL, "\x1b[41m"),
    ]

    FORMATS = {
        level: logging.Formatter(
            f"\x1b[30;1m[%(asctime)s]\x1b[0m {colour}%(levelname)s\x1b[0m \x1b[35m%(name)s (%(filename)s:%(lineno)d):\x1b[0m \x1b[0m%(message)s",
            "%Y-%m-%d %H:%M:%S %z",
        )
        for level, colour in LEVEL_COLOURS
    }

    def format(self, record):
        if record.name in ["STDOUT", "STDERR"]:
            formatter = logging.Formatter(
                "\x1b[30;1m[%(asctime)s]\x1b[0m \x1b[34;1m%(levelname)s\x1b[0m \x1b[35m%(name)s:\x1b[0m \x1b[0m%(message)s",
                "%Y-%m-%d %H:%M:%S %z",
            )
        else:
            formatter = self.FORMATS.get(record.levelno)

        if formatter is None:
            formatter = self.FORMATS[logging.DEBUG]

        # Override the traceback to always print in red
        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = f"\x1b[31m{text}\x1b[0m"

        output = formatter.format(record)

        # Remove the cache layer
        record.exc_text = None
        return output


class StreamToLogger(object):
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.linebuf = ""

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass


class LogPath:
    LOG_FILE_PATH = f"{USER_DATA_PATH}\\logs\\bot\\mkbot-{int(time.time())}.log"

    @classmethod
    def get(cls):
        return cls.LOG_FILE_PATH

    @classmethod
    def update(cls):
        cls.LOG_FILE_PATH = f"{USER_DATA_PATH}\\logs\\bot\\mkbot-{int(time.time())}.log"


def delete_old_logs(log, max_count=20):
    p = f"{USER_DATA_PATH}\\logs\\bot\\mkbot-*.log"
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
    log = logging.getLogger()
    log.propagate = True
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s (%(filename)s:%(lineno)d): %(message)s",
        "%Y-%m-%d %H:%M:%S %z",
    )
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(LOG_LEVEL)
    stream_handler.setFormatter(ColorFormatter())
    file_handler = logging.FileHandler(file_path, mode="w", encoding="utf-8")
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)
    log.addHandler(stream_handler)
    log.addHandler(file_handler)
    log.setLevel(LOG_LEVEL)

    discord_log = logging.getLogger("discord")
    discord_log.setLevel(logging.WARNING)

    # sys.stdout = StreamToLogger(logging.getLogger("STDOUT"), logging.INFO)
    # sys.stderr = StreamToLogger(logging.getLogger("STDERR"), logging.ERROR)

    # logger = logging.getLogger("discord")
    # logger.setLevel(logging.DEBUG)
    # logger.addHandler(stream_handler)

    if cleanup:
        delete_old_logs(log)


def get_logger(name):
    log = logging.getLogger(f"mkbot.{name}")
    return log
