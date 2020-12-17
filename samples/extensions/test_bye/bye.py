# Test MK Bot Extension
from discord.ext import commands


def setup(bot):
    @commands.command()
    @bot.MGCert.verify(2)
    async def bye(ctx):
        await ctx.send('Bye {0.display_name}.'.format(ctx.author))
    bot.add_command(bye)


def teardown(bot):
    print('I am being unloaded!')
