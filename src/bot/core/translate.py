from discord.ext import commands
import discord
import requests
from .utils.config import CONFIG
from langdetect import detect


def setup(bot: commands.Bot):
    @commands.command(aliases=['trans'])
    @bot.MGCert.verify(2)
    async def translate(ctx, msg, targetLang='en'):
        """
        입력한 문장을 원하는 언어로 번역하는 명령어입니다.
        번역 가능 언어:
                        한국어	kr
                        영어	en
                        일본어	jp
                        중국어	cn
                        베트남어	vi
                        인도네시아어	id
                        아랍어	ar
                        뱅갈어	bn
                        독일어	de
                        스페인어	es
                        프랑스어	fr
                        힌디어	hi
                        이탈리아어	it
                        말레이시아어	ms
                        네덜란드어	nl
                        포르투갈어	pt
                        러시아어	ru
                        태국어	th
                        터키어	tr

        {commandPrefix}translate "번역하면 무슨 뜻?" english
        {commandPrefix}translate "번역하면 무슨 뜻?" en
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
            await channel.send(embed=bot.replyformat.get(ctx, '번역 실패: 입력 언어 감지 실패', '감지된 언어가 지원되지 않습니다. \n ** 감지된 언어: ' + srcLang + ' **\n//help translate로 지원언어 목록을 확인하세요'))
            raise commands.CommandError(
                "srcLanguage detected is not supported")

        if targetLang.lower() in languages:
            targetLang = languages[targetLang.lower()]

        elif not targetLang in languages.values():
            await channel.send(embed=bot.replyformat.get(ctx, '번역 실패: 출력 언어 없음', '입력한 출력언어를 찾을 수 없습니다!'))
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

        await channel.send(embed=bot.replyformat.get(ctx, '번역 성공: ' + srcLang + ' => ' + targetLang, msg + '\n\n' + response.json()['translated_text'][0][0]))

    bot.add_command(translate)
