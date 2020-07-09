import discord
import datetime
from APIKey import TOKEN


Msg_Color = None


def get_color():
    global Msg_Color
    if Msg_Color == None:
        c = TOKEN.get('MESSAGE_COLOR', '#FAA61A')
        c = c.replace('#', '')
        Msg_Color = int(c, 16)
        return Msg_Color
    else:
        return Msg_Color


class MsgFormatter:
    def __init__(self, avatar_url):
        self.avatar_url = avatar_url

    def get(self, ctx, title, description='', show_req_user=True):
        embed = discord.Embed(title=title, description=description +
                              '\n\nPowered by [MK Bot](https://gitlab.com/mgylabs/discord-bot)', color=get_color(), timestamp=datetime.datetime.utcnow())
        if show_req_user:
            embed.add_field(name='Requested by',
                            value='<@{}>'.format(ctx.author.id))
        embed.set_footer(text='© 2020 MGYL', icon_url=self.avatar_url)
        return embed
