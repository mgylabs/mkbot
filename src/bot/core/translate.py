from discord.ext import commands
import discord
import requests
from .utils.config import CONFIG
from langdetect import detect


def setup(bot: commands.Bot):
    @commands.command(aliases=['trans'])
    @bot.MGCert.verify(2)
    async def translate(ctx: commands.Context, msg, targetLang='en'):
        """
        Command that translates sentence entered to desired language 
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

        {commandPrefix}translate "What does it mean in English?" english
        {commandPrefix}translate "What does it mean in English?" en
        """
        channel = ctx.message.channel
        srcLang = detect(msg)
        languages = {"korean": "kr",
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

        langDetectDict = {
            "ko": "kr",
            "ja": "jp",
            "zh": "cn", }

        if srcLang in langDetectDict:
            srcLang = langDetectDict[srcLang]

        if not srcLang in languages.values():
            await channel.send(embed=bot.replyformat.get(ctx, 'Translation Fail: Input Language Detection Failed', 'Language detected is not supported. \n ** Detected language: ' + srcLang + ' **\nuse //help translate to find supported languages'))
            raise commands.CommandError(
                "srcLanguage detected is not supported")

        if targetLang.lower() in languages:
            targetLang = languages[targetLang.lower()]

        elif not targetLang in languages.values():
            await channel.send(embed=bot.replyformat.get(ctx, 'Translation Fail: Target language not existing', 'Cannot find target language inputted'))
            raise commands.CommandError("targetlang not identified")

        headers = {
            'Authorization': 'KakaoAK ' + CONFIG.kakaoToken
        }
        params = {
            'query': msg,
            'src_lang': srcLang,
            'target_lang': targetLang
        }
        response = requests.get(
            'https://kapi.kakao.com/v1/translation/translate', headers=headers, params=params)

        await channel.send(embed=bot.replyformat.get(ctx, 'Translation Successful: ' + srcLang + ' => ' + targetLang, msg + '\n\n' + response.json()['translated_text'][0][0]))

    bot.add_command(translate)
