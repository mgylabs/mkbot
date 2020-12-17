import discord
import datetime
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
    def get(ctx, title, description='', show_req_user=True):
        embed = discord.Embed(title=title, description=description +
                              '\n\nPowered by [MK Bot](https://github.com/mgylabs/mulgyeol-mkbot)', color=get_color(), timestamp=datetime.datetime.utcnow())
        if show_req_user:
            embed.add_field(name='Requested by',
                            value='<@{}>'.format(ctx.author.id))
        embed.set_footer(text='© 2020 MGYL', icon_url=MsgFormatter.avatar_url)
        return embed
