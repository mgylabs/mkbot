import datetime

import discord

from .config import CONFIG

Msg_Color = None


def get_color():
    global Msg_Color
    if Msg_Color == None:
        c = CONFIG.messageColor
        c = c.replace('#', '')
        Msg_Color = int(c, 16)
        return Msg_Color
    else:
        return Msg_Color


class MsgFormatter:
    avatar_url: str = None

    @staticmethod
    def set_avatar_url(avatar_url):
        MsgFormatter.avatar_url = avatar_url

    @staticmethod
    def get(ctx, title, description='', fields: list = [], show_req_user=True, *, color: str = None):
        if color is None:
            color = get_color()
        else:
            color = int(color.replace('#', ''), 16)

        embed = discord.Embed(title=title, description=description +
                              '\n\nPowered by [MK Bot](https://github.com/mgylabs/mulgyeol-mkbot)', color=color, timestamp=datetime.datetime.utcnow())

        for fd in fields:
            embed.add_field(**fd)

        if show_req_user:
            embed.add_field(name='Requested by',
                            value='<@{}>'.format(ctx.author.id))
        embed.set_footer(text='© 2020 MGYL', icon_url=MsgFormatter.avatar_url)
        return embed

    @staticmethod
    def push(title, description='', fields: list = []):
        embed = discord.Embed(title=title, description=description, color=get_color(
        ), timestamp=datetime.datetime.utcnow())

        for fd in fields:
            embed.add_field(**fd)

        embed.set_footer(text='© 2020 MGYL', icon_url=MsgFormatter.avatar_url)
        return embed
