# Test MK Bot Extension
from discord.ext import commands


async def setup(bot):
    @commands.command()
    @bot.MGCert.verify(2)
    async def bye(ctx):
        await ctx.send("Bye {0.display_name}.".format(ctx.author))

    await bot.add_command(bye)


def teardown(bot):
    print("I am being unloaded!")
