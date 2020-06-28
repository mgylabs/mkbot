import discord
import datetime


class Color:
    Yellow = 0xFAA61A
    Blue = 0x7289DA


class MsgFormatter:
    def __init__(self, avatar_url):
        self.avatar_url = avatar_url

    def get(self, ctx, title, description='', show_req_user=True):
        embed = discord.Embed(title=title, description=description +
                              '\n\nPowered by [MK Bot](https://gitlab.com/mgylabs/discord-bot)', color=Color.Yellow, timestamp=datetime.datetime.utcnow())
        if show_req_user:
            embed.add_field(name='Requested by',
                            value='<@{}>'.format(ctx.author.id))
        embed.set_footer(text='© 2020 MGYL', icon_url=self.avatar_url)
        return embed
