from discord.ext import commands
import discord
import random
import time


def setup(bot: commands.Bot):
    @commands.command(aliases=['rou'])
    @bot.MGCert.verify(2)
    async def roulette(ctx: commands.Context, title, *items):
        """
        Play roulette

        Examples:
        {commandPrefix}roulette "Player" @user1 @user2 @user3
        {commandPrefix}rou "title" "item 1" "item 2"

        Note:
        This bot cannot be added to items.
        """
        msg: discord.Message = await ctx.send(embed=bot.replyformat.get(ctx, "Roulette is running. Please wait.", "..."))

        for i in range(5, 0, -1):
            await msg.edit(embed=bot.replyformat.get(ctx, "Roulette is running. Please wait.", f"{i} sec left"))
            time.sleep(1)

        await msg.edit(embed=bot.replyformat.get(
            ctx, f"Roulette for {title}", f"chose... {random.choice(items)}!"))

    bot.add_command(roulette)
