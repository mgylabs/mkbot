from distutils.util import strtobool

import discord
import requests
from discord.ext import commands
from langdetect import detect

from .utils import listener
from .utils.config import CONFIG
from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter


class Translate(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.conversation = False
        self.target = {'en'}
        self.languages = {"korean": "kr",
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
                          "turkish": "tr"}

    @commands.Cog.listener()
    @listener.on_message()
    async def on_message(self, message: discord.Message):
        if (not self.conversation):
            return

        ctx = await self.bot.get_context(message)
        _, result = await self._trans(ctx, message.content, self.target)
        if len(result) > 1:
            await ctx.send('\n'.join([f"{k.upper()}: {v}" for k, v in result.items()]))
        else:
            await ctx.send('\n'.join([f"{v}" for _, v in result.items()]))

    @commands.command(aliases=['trans'])
    @MGCertificate.verify(level=Level.TRUSTED_USERS)
    async def translate(self, ctx: commands.Context, *args):
        """
        Command that translates sentence entered to desired language. 
        Language list:
                        Korean	       kr
                        English	       en
                        Japanese	   jp
                        Chinese	       cn
                        Vietnamese	   vi
                        Inodonesian	   id
                        Arabic	       ar
                        Bengali	       bn
                        German	       de
                        Spanish	       es
                        French	       fr
                        Hindi	       hi
                        Italian	       it
                        Malay	       ms
                        Dutch	       nl
                        Portuguese	   pt
                        Russian	       ru
                        Thai	       th
                        Turkish	       tr

        {commandPrefix}translate "What does it mean in Korean?" korean
        {commandPrefix}translate "What does it mean in Korean?" kr

        * Conversation Mode (beta)
        --conversation <true_or_false>
            You can also use <t_or_f>, <y_or_n> and <on_or_off>.
        --target <languages>
            You can either give multiple languages separated by comma (,).

        Activate
        {commandPrefix}translate --conversation true --target en
        {commandPrefix}translate --conversation true --target en,jp,kr

        Deactivate
        {commandPrefix}translate --conversation false
        """

        if '--conversation' in args:
            try:
                self.conversation = strtobool(
                    args[args.index('--conversation') + 1])
            except ValueError as e:
                await ctx.send(embed=MsgFormatter.get(
                    ctx, 'Usage Error', str(e)))
            if '--target' in args:
                targetLangs = set(
                    args[args.index('--target') + 1].split(','))
                self.target = await self._convert_langs(ctx, targetLangs)
            if self.conversation:
                await ctx.send(embed=MsgFormatter.get(
                    ctx, 'Start Conversation Mode', f'All messages are automatically translated to {", ".join([x.upper() for x in sorted(self.target)])}.'))
            else:
                await ctx.send(embed=MsgFormatter.get(
                    ctx, 'Exit Conversation Mode'))
            return
        else:
            msg = args[0]
            targetLangs = {args[1]} if len(args) > 1 else self.target

        srcLang, result = await self._trans(ctx, msg, await self._convert_langs(ctx, targetLangs))
        for t, r in result.items():
            await ctx.send(embed=MsgFormatter.get(ctx, 'Translation Successful ' + srcLang + ' => ' + t, msg + '\n\n' + r))

    async def _convert_langs(self, ctx, langs: set):
        short_langs = {t for t in langs if t.lower()
                       in self.languages}
        langs = (
            langs - short_langs) | {self.languages[t] for t in short_langs}
        invalid_langs = {t for t in langs if not (
            t in self.languages.values())}
        langs -= invalid_langs

        if len(langs) == 0:
            await ctx.send(embed=MsgFormatter.get(ctx, f'Translation Fail: {", ".join(invalid_langs)}', 'Cannot find target language(s) inputted'))
            raise commands.CommandError("targetlang not identified")
        elif len(invalid_langs) > 0:
            await ctx.send(embed=MsgFormatter.get(ctx, f'Translation Warning: {", ".join(invalid_langs)}', 'Cannot find target language(s) inputted'))

        return langs

    async def _trans(self, ctx, msg, targetLangs: set):
        channel = ctx.message.channel
        srcLang = detect(msg)

        langDetectDict = {
            "ko": "kr",
            "ja": "jp",
            "zh": "cn", }

        if srcLang in langDetectDict:
            srcLang = langDetectDict[srcLang]

        if not srcLang in self.languages.values():
            await channel.send(embed=MsgFormatter.get(ctx, 'Translation Fail: Input Language Detection Failed', 'Language detected is not supported. \n ** Detected language: ' + srcLang + ' **\nuse //help translate to find supported languages'))
            raise commands.CommandError(
                "srcLanguage detected is not supported")

        result = {}
        headers = {
            'Authorization': 'KakaoAK ' + CONFIG.kakaoToken
        }

        for t in targetLangs:
            if t != srcLang:
                params = {
                    'query': msg,
                    'src_lang': srcLang,
                    'target_lang': t
                }
                response = requests.get(
                    'https://kapi.kakao.com/v1/translation/translate', headers=headers, params=params)
                result[t] = response.json()['translated_text'][0][0]

        return srcLang, result


def setup(bot: commands.Bot):
    bot.add_cog(Translate(bot))
