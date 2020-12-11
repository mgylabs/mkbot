from discord.ext import commands


def setup(bot: commands.Bot):
    @commands.command()
    @bot.MGCert.verify(1)
    async def logout(ctx: commands.Context):
        """
        Terminates bot (Requires Admin Permission)
        """
        await ctx.send(embed=bot.replyformat.get(ctx, "Logs out of Discord and closes all connections"))
        print('Logged out')
        await bot.logout()

    bot.add_command(logout)