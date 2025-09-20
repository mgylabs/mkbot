import contextvars
import gettext
from typing import Callable

from discord.app_commands import locale_str
from discord.ext import commands

from mgylabs.utils import logger

from .paths import LOCALE_DIR
from .utils import get_user_locale_code

log = logger.get_logger(__name__)


class I18nExtension:
    default_i18n_instance = None

    def __init__(self, default=True) -> None:
        self.bot = None
        self._current_locale = contextvars.ContextVar("_current_locale")

        if default or I18nExtension.default_i18n_instance is None:
            I18nExtension.default_i18n_instance = self

    def init_bot(self, bot: commands.Bot, get_locale_func: Callable):
        self._bot = bot

        async def pre(ctx):
            self.set_current_locale(get_locale_func(ctx))

        self._bot.before_invoke(pre)

    def set_current_locale(self, locale: str) -> str:
        self._current_locale.set(locale)

    def get_current_locale(self) -> str:
        try:
            result = self._current_locale.get()
        except LookupError:
            log.warning(
                "current_locale is not set. Content is translated to the default locale."
            )
            result = "en"

        return result

    @classmethod
    def set_current_locale_by_user(cls, user_id):
        i18n = cls.default_i18n_instance

        i18n.set_current_locale(get_user_locale_code(user_id))

    @classmethod
    def change_current_locale(cls, locale: str):
        i18n = cls.default_i18n_instance

        i18n.set_current_locale(locale)

    @classmethod
    def gettext_lazy(cls, message):
        return message

    @classmethod
    def get_translation(cls, locale=None, fallback=True):
        i18n = cls.default_i18n_instance

        if i18n is None:
            raise NameError("No default i18n instance has been initialized!")

        if locale is None:
            languages = None
        else:
            languages = [locale]

        t = gettext.translation(  # @IgnoreException
            "mkbot", LOCALE_DIR, languages, fallback=fallback
        )

        return t

    @classmethod
    def gettext(cls, message, locale=None, fallback=True):
        t = cls.get_translation(locale, fallback)  # @IgnoreException
        return t.gettext(message)

    @classmethod
    def namespaced_gettext(cls, message: str, locale=None, fallback=True):
        t = cls.get_translation(locale, fallback)  # @IgnoreException

        text = t.gettext(message)
        namespace, translated = text.split("|", 1)

        return translated

    @classmethod
    def get_contextual_translation(cls, fallback=True):
        i18n = cls.default_i18n_instance

        if i18n is None:
            raise NameError("No default i18n instance has been initialized!")

        locale = i18n.get_current_locale()

        if locale is None:
            languages = None
        else:
            languages = [locale]

        t = gettext.translation("mkbot", LOCALE_DIR, languages, fallback=fallback)

        return t

    @classmethod
    def contextual_gettext(cls, message):
        t = cls.get_contextual_translation()
        return t.gettext(message)

    @classmethod
    def contextual_ngettext(cls, msgid1: str, msgid2: str, n: int):
        t = cls.get_contextual_translation()
        return t.ngettext(msgid1, msgid2, n)

    @classmethod
    def contextual_namespaced_gettext(cls, message: str):
        t = cls.get_contextual_translation()

        text = t.gettext(message)
        namespace, translated = text.split("|", 1)

        return translated


class NamespacedLocaleStr(locale_str):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, **kwargs)

    @property
    def message(self) -> str:
        namespace, msg = super().message.split("|", 1)
        return msg
