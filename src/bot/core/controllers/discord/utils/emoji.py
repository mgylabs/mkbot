from mgylabs.utils.config import CONFIG


class MetaEmoji(type):
    def __getattribute__(cls, name):
        if name in CONFIG.emoji:
            return CONFIG.emoji[name]
        else:
            return super().__getattribute__(name)


class Emoji(metaclass=MetaEmoji):
    typing = "<a:typing:1073250215974420490>"
    command = "<:command:1201509794897465354>"
    generating = "<a:generating:1398610240228032512>"
    GenAI = "<:GenAI:1398611276917248180>"
