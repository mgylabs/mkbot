import asyncio
from functools import wraps
import logging

logger = logging.getLogger('Logger')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s :: %(asctime)s :: %(message)s", "%Y-%m-%d %H:%M:%S")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
file_handler = logging.FileHandler('MK Bot.log', mode='a')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class MGCertificate:
    cert_users = ['Mycroft#5224', 'EMATEN#2245']
    
    @staticmethod
    def verify(func):
        @wraps(func)
        async def outerfunc(ctx, *args, **kwargs):
            req_user = '{}#{}'.format(ctx.author.display_name, ctx.author.discriminator)
            if req_user in MGCertificate.cert_users:
                return await func(ctx, *args, **kwargs)
            else:
                await ctx.send('{}은(는) 신뢰할 수 있는 사용자 목록에 등록되어 있지 않습니다.\n이 시도를 보고합니다.'.format(req_user))
                logger.critical('An untrusted user {} tried to command.'.format(req_user))
                raise Exception('Untrusted user')
        return outerfunc
        