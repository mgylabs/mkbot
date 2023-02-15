from mkbot_nlu.nlu import MKBotNLU
from mkbot_nlu.utils import Intent

from mgylabs.utils import logger

log = logger.get_logger(__name__)


class NluModel:
    nlu = None

    @classmethod
    def load(cls):
        if cls.nlu is not None:
            return

        try:
            cls.nlu = MKBotNLU()
        except ModuleNotFoundError as error:
            log.warning(f"mkbot-nlu is not available: {error}")
            raise
        except Exception as error:
            log.exception(error)
            raise

    @classmethod
    def unload(cls):
        del cls.nlu
        cls.nlu = None

    @classmethod
    async def parse(cls, text: str) -> Intent:
        return await cls.nlu.parse(text)
