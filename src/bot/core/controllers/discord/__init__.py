import logging

from mgylabs.utils.config import is_development_mode


class DiscordFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not record.name.startswith("discord")


log = logging.getLogger()
formatter = logging.Formatter(
    "[%(asctime)s] %(name)s (line %(lineno)d): %(levelname)s - %(message)s",
    "%Y-%m-%d %H:%M:%S",
)
stream_handler = logging.StreamHandler()
stream_handler.addFilter(DiscordFilter())
if is_development_mode():
    LOG_LEVEL = logging.DEBUG
else:
    LOG_LEVEL = logging.WARNING
stream_handler.setLevel(LOG_LEVEL)
stream_handler.setFormatter(formatter)
log.addHandler(stream_handler)
log.setLevel(LOG_LEVEL)
