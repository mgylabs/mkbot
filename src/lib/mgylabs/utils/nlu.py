from mkbot_nlu.nlu import MKBotNLU
from mkbot_nlu.utils import Intent

from mgylabs.utils import logger

log = logger.get_logger(__name__)


class NluModel:
    nlu = None

    @classmethod
    def load(cls, block=False):
        if cls.nlu is None:
            cls.nlu = MKBotNLU()

        if cls.nlu.loader and cls.nlu.loader.is_alive():
            return

        try:
            cls.nlu.start()

            if block:
                cls.nlu.ready_event.wait()
        except Exception as error:
            log.exception(error)
            raise

    @classmethod
    def unload(cls):
        if cls.nlu is None:
            return

        cls.nlu.terminate()

    @classmethod
    async def parse(cls, text: str) -> Intent:
        if not cls.nlu.is_ready():
            return None

        return await cls.nlu.parse(text)
