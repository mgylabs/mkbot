import asyncio
from typing import Dict, List, Optional

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from langdetect import detect

from core.controllers.discord.utils.command_helper import send
from mgylabs.i18n import _L, __
from mgylabs.utils import logger
from mgylabs.utils.config import CONFIG

from .utils import listener
from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter

log = logger.get_logger(__name__)


class Translate(commands.Cog):
    conversation_group = app_commands.Group(
        name="conversation", description=_L("Conversational translation mode")
    )
    targets: Dict[int, set] = {}
    languages = {
        "korean": "kr",
        "english": "en",
        "japanese": "jp",
        "chinese": "cn",
        "vietnamese": "vi",
        "indonesian": "id",
        "arabic": "ar",
        "bengali": "bn",
        "german": "de",
        "spanish": "es",
        "french": "fr",
        "hindi": "hi",
        "italian": "it",
        "malay": "ms",
        "dutch": "nl",
        "portuguese": "pt",
        "russian": "ru",
        "thai": "th",
        "turkish": "tr",
    }

    def __init__(self, bot):
        self.bot = bot
        self.conversation_flag = False

    @commands.Cog.listener()
    @listener.on_message()
    async def on_message(self, message: discord.Message):
        if len(self.targets) == 0:
            return

        ctx: commands.Context = await self.bot.get_context(message)

        if ctx.channel.id not in self.targets:
            return

        t = self.targets[ctx.channel.id]

        _, result, _ = await self._trans(ctx, message.content, t)
        if len(result) > 1:
            await ctx.send("\n".join([f"{k.upper()}: {v}" for k, v in result.items()]))
        elif len(result) == 1:
            await ctx.send("\n".join([f"{v}" for _, v in result.items()]))

    @conversation_group.command()
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def enable(self, interaction: discord.Interaction, target: str):
        """
        Enables conversational translation mode.
        """
        t = await self._convert_langs(interaction, {target})

        if interaction.channel_id in self.targets:
            self.targets[interaction.channel_id].update(t)
        else:
            self.targets[interaction.channel_id] = t

        await send(
            interaction,
            embed=MsgFormatter.get(
                interaction,
                __("Conversation Mode"),
                __("All messages are automatically translated to {0}.").format(
                    ", ".join(
                        [
                            x.upper()
                            for x in sorted(self.targets[interaction.channel_id])
                        ]
                    )
                ),
            ),
        )

    @conversation_group.command()
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def disable(self, interaction: discord.Interaction, target: str):
        """
        Disables conversational translation mode.
        """
        if interaction.channel_id in self.targets:
            if target == "all":
                del self.targets[interaction.channel_id]

                await send(
                    interaction,
                    embed=MsgFormatter.get(
                        interaction,
                        __("Conversation mode was disabled"),
                    ),
                )
            else:
                t = await self._convert_langs(interaction, {target})
                self.targets[interaction.channel_id].remove(list(t)[0])

                await send(
                    interaction,
                    embed=MsgFormatter.get(
                        interaction,
                        __("Conversation Mode"),
                        __("All messages are automatically translated to {0}.").format(
                            ", ".join(
                                [
                                    x.upper()
                                    for x in sorted(
                                        self.targets[interaction.channel_id]
                                    )
                                ]
                            )
                        ),
                    ),
                )

    @commands.hybrid_command(aliases=["trans"], hidden=True)
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def translate(
        self, ctx: commands.Context, query: str, target: Optional[str] = "en"
    ):
        """
        Command that translates sentence entered to desired language
        """

        srcLang, result, success = await self._trans(
            ctx, query, await self._convert_langs(ctx, {target})
        )
        if success:
            for t, r in result.items():
                await ctx.send(
                    embed=MsgFormatter.get(
                        ctx,
                        __("Translation Successful {srcLang} -> {result}").format(
                            srcLang=srcLang, result=t
                        ),
                        query + "\n\n" + r,
                    ),
                )

    @translate.autocomplete("target")
    @enable.autocomplete("target")
    async def conversation_enable_target_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> List[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=k.capitalize(), value=v)
            for k, v in self.languages.items()
            if current.lower() in k.lower()
        ]

    @disable.autocomplete("target")
    async def conversation_disable_target_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> List[app_commands.Choice[str]]:
        ls = [
            app_commands.Choice(name=k.capitalize(), value=v)
            for k, v in self.languages.items()
            if current.lower() in k.lower()
        ]

        ls.insert(0, app_commands.Choice(name="All", value="all"))

        return ls

    async def _convert_langs(self, ctx, langs: set):
        short_langs = {t for t in langs if t.lower() in self.languages}
        langs = (langs - short_langs) | {self.languages[t] for t in short_langs}
        invalid_langs = {t for t in langs if not (t in self.languages.values())}
        langs -= invalid_langs

        if len(langs) == 0:
            await send(
                ctx,
                embed=MsgFormatter.get(
                    ctx,
                    __("Translation Fail: {0}").format(", ".join(invalid_langs)),
                    __("Cannot find target language(s) inputted"),
                ),
            )
            log.warning("targetlang not identified")
        elif len(invalid_langs) > 0:
            await send(
                ctx,
                embed=MsgFormatter.get(
                    ctx,
                    __("Translation Warning: {0}").format(", ".join(invalid_langs)),
                    __("Cannot find target language(s) inputted"),
                ),
            )
        return langs

    async def _trans(self, ctx, msg, targetLangs: set):
        success = True
        srcLang = detect(msg)

        langDetectDict = {
            "ko": "kr",
            "ja": "jp",
            "zh": "cn",
        }

        result = {}
        headers = {
            "Authorization": "KakaoAK " + CONFIG.kakaoToken,
        }

        if srcLang in langDetectDict:
            srcLang = langDetectDict[srcLang]

        if srcLang not in self.languages.values():
            await send(
                ctx,
                embed=MsgFormatter.get(
                    ctx,
                    __("Translation Fail: Input Language Detection Failed"),
                    __(
                        "Language detected is not supported. \n ** Detected language: {srcLang} **\nuse //help translate to find supported languages"
                    ).format(srcLang=srcLang),
                ),
            )
            log.warning("srcLanguage detected is not supported")
            return srcLang, result, False

        tasks = [
            self._request_api(
                headers, {"query": msg, "src_lang": srcLang, "target_lang": t}
            )
            for t in targetLangs
            if t != srcLang
        ]
        result = dict(await asyncio.gather(*tasks))

        return srcLang, result, success

    async def _request_api(self, headers, params):
        async with aiohttp.ClientSession(
            headers=headers, raise_for_status=True
        ) as session:
            async with session.get(
                "https://dapi.kakao.com/v2/translation/translate", params=params
            ) as r:
                js = await r.json()
                return params["target_lang"], js["translated_text"][0][0]


ko2langcode = {
    "한국어": "kr",
    "영어": "en",
    "일본어": "jp",
    "중국어": "cn",
    "베트남어": "vi",
    "인도네시아어": "id",
    "아랍어": "ar",
    "벵골어": "bn",
    "독일어": "de",
    "스페인어": "es",
    "프랑스어": "fr",
    "힌디어": "hi",
    "이탈이아어": "it",
    "말레이어": "ms",
    "네덜란드어": "nl",
    "포르투갈어": "pt",
    "러시아어": "ru",
    "태국어": "th",
    "터키어": "tr",
}


# @register_intent("command::translate::translate", "translate")
# def cmd_translate(intent: Intent):
#     query = intent.get_an_entity("trans_query")
#     lang = intent.get_an_entity("language")

#     if query:
#         return f'translate "{intent.get_an_entity("trans_query")}" {ko2langcode.get(lang, "en")}'
#     else:
#         return None


async def setup(bot: commands.Bot):
    await bot.add_cog(Translate(bot))
