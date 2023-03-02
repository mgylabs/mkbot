import asyncio

import discord
from discord.ext import commands

from core.controllers.discord.utils import Emoji, api
from mgylabs.i18n import _
from mgylabs.utils import logger
from mgylabs.utils.config import CONFIG
from mgylabs.utils.nlu import NluModel

from .utils.MGCert import Level, MGCertificate

log = logger.get_logger(__name__)


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.install_working = set()
        self.load_working = set()
        self.unload_working = set()

    async def load_nlu_model(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, NluModel.load, True)

    @commands.command(hidden=True)
    @MGCertificate.verify(level=Level.ADMIN_USERS)
    async def install(self, ctx: commands.Context, *, query):
        if query in self.install_working:
            return

        self.install_working.add(query)

        if query == "nlu_ko":
            msg: discord.Message = await ctx.send(
                f"{Emoji.typing} " + _("Installing... `%s`") % query
            )

            from mkbot_nlu.nlu import MKBotNLU

            log.info(f"Downloading {query}...")
            await MKBotNLU.download_ko_model(f"{api.extensions_path}/{query}")

            CONFIG.enabledChatMode = True
            api.set_enabled(query)

            log.info(f"Loading {query}...")

            try:
                await self.load_nlu_model()
            except Exception as error:
                await msg.edit(
                    content=_("🟡 Successfully installed `%s`, but failed to load.")
                    % query
                    + f"\n{error}"
                )
            else:
                log.info(f"Successfully installed {query}...")
                await msg.edit(content=_("🟢 Successfully installed `%s`.") % query)
        else:
            await ctx.send("Invalid!")

        self.install_working.remove(query)

    @commands.command(hidden=True)
    @MGCertificate.verify(level=Level.ADMIN_USERS)
    async def load(self, ctx: commands.Context, *, query):
        if query in self.load_working:
            return

        self.load_working.add(query)

        if query == "nlu_ko":
            msg: discord.Message = await ctx.send(
                f"{Emoji.typing} " + _("Loading... `%s`") % query
            )

            CONFIG.enabledChatMode = True
            api.set_enabled(query)

            log.info(f"Loading {query}...")
            try:
                await self.load_nlu_model()
            except Exception as error:
                log.exception(error)
                await msg.edit(content=_("🔴 Failed to load `%s`") % query)
            else:
                log.info(f"Successfully loaded {query}...")
                await msg.edit(content=_("🟢 Successfully loaded `%s`") % query)
        else:
            await ctx.send("Invalid!")

        self.load_working.remove(query)

    @commands.command(hidden=True)
    @MGCertificate.verify(level=Level.ADMIN_USERS)
    async def unload(self, ctx: commands.Context, *, query):
        if query in self.load_working:
            return

        self.unload_working.add(query)

        if query == "nlu_ko":
            msg = await ctx.send(f"{Emoji.typing} " + _("Unloading... `%s`") % query)

            log.info(f"Unloading {query}...")
            NluModel.unload()
            log.info(f"Successfully unloaded {query}...")

            await msg.edit(content=_("🟢 Successfully unloaded `%s`") % query)
        else:
            await ctx.send("Invalid!")

        self.unload_working.remove(query)


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))