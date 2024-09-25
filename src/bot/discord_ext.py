import platform

discord_extensions = (
    "core.controllers.discord.act",
    "core.controllers.discord.dev",
    # "core.controllers.discord.admin",
    "core.controllers.discord.delete",
    "core.controllers.discord.join",
    "core.controllers.discord.leave",
    "core.controllers.discord.logout",
    "core.controllers.discord.ping",
    "core.controllers.discord.voice",
    "core.controllers.discord.poll",
    "core.controllers.discord.roulette",
    "core.controllers.discord.dice",
    # "core.controllers.discord.translate",
    "core.controllers.discord.tic_tac_toe",
    "core.controllers.discord.feedback",
    "core.controllers.discord.timezone",
    "core.controllers.discord.clock",
    "core.controllers.discord.dday",
    "core.controllers.discord.lotto",
    "core.controllers.discord.minigames",
    "core.controllers.discord.language",
    "core.controllers.discord.google",
    "core.controllers.discord.url",
    "core.controllers.discord.news",
)


if not (platform.uname().machine.startswith("iP")):
    discord_extensions += ("core.controllers.discord.music",)
