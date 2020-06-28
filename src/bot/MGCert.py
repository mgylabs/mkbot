import asyncio
from functools import wraps
import logging
import json
from MsgFormat import MsgFormatter

logger = logging.getLogger('Logger')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(levelname)s :: %(asctime)s :: %(message)s", "%Y-%m-%d %H:%M:%S")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
file_handler = logging.FileHandler('MK Bot.log', mode='a')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class Level:
    ALL_USERS = 0
    CERT_USERS = 1
    ADMIN_USERS = 2

    @staticmethod
    def get_description(num):
        if num == Level.ALL_USERS:
            return Level.Description.ALL_USERS
        elif num == Level.CERT_USERS:
            return Level.Description.CERT_USERS
        else:
            return Level.Description.ADMIN_USERS

    class Description:
        ALL_USERS = '모든 사용자'
        CERT_USERS = '신뢰할 수 있는 사용자'
        ADMIN_USERS = '관리자'


class MGCertificate:
    def __init__(self, name):
        with open(name, 'rt') as f:
            data = json.load(f)
        self.admin_users = data['admin_users']
        self.cert_users = data['trusted_users'] + self.admin_users

    def verify(self, level=Level.CERT_USERS):
        def deco(func):
            @wraps(func)
            async def outerfunc(ctx, *args, **kwargs):
                req_user = str(ctx.author)
                if level != Level.ALL_USERS:
                    if level == Level.CERT_USERS:
                        rusers = self.cert_users
                    else:
                        rusers = self.admin_users

                    if (len(rusers) != 0):
                        if not (req_user in rusers):
                            replyformat = MsgFormatter(ctx.me.avatar_url)
                            embed = replyformat.get(ctx, "Permission denied", '사용자 <@{}>은(는) {} 목록에 등록되어 있지 않습니다. 이 시도를 보고합니다.'.format(
                                ctx.author.id, Level.get_description(level)), False)
                            embed.add_field(name='User', value=str(ctx.author))
                            embed.add_field(name='Command tried', value='{} ({})'.format(
                                ctx.command.name, Level.get_description(level)))
                            await ctx.send(embed=embed)
                            logger.critical('{} tried to command that needs "{}" permission.'.format(
                                req_user, Level.get_description(level)))
                            raise Exception('Untrusted user')

                return await func(ctx, *args, **kwargs)

            return outerfunc
        return deco
