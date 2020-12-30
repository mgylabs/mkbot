import logging

from .utils.config import is_development_mode


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
    stream_handler.setLevel(logging.DEBUG)
else:
    stream_handler.setLevel(logging.WARNING)
stream_handler.setFormatter(formatter)
log.addHandler(stream_handler)
