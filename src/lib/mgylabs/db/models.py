import sqlalchemy
from babel import Locale
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class HashStore(Base):
    __tablename__ = "hash_store"

    key = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    value = sqlalchemy.Column(sqlalchemy.String)
    update_at = sqlalchemy.Column(
        sqlalchemy.DateTime, default=func.now(), onupdate=func.now()
    )
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=func.now())


class DiscordUser(Base):
    __tablename__ = "discord_users"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    locale = sqlalchemy.Column(sqlalchemy.String)
    timezone = sqlalchemy.Column(sqlalchemy.String, default="UTC", nullable=False)
    last_used_at = sqlalchemy.Column(sqlalchemy.DateTime, default=func.now())
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=func.now())

    def get_language_name(self):
        if self.locale is None:
            return "English"
        else:
            return Locale.parse(self.locale).get_language_name()


class DiscordBotRequestLog(Base):
    __tablename__ = "discord_bot_request_logs"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    bot_id = sqlalchemy.Column(sqlalchemy.Integer)
    user_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey(DiscordUser.id)
    )
    msg_id = sqlalchemy.Column(sqlalchemy.Integer, unique=True)
    guild_id = sqlalchemy.Column(sqlalchemy.Integer)
    channel_id = sqlalchemy.Column(sqlalchemy.Integer)
    user_perm = sqlalchemy.Column(sqlalchemy.Integer)
    command = sqlalchemy.Column(sqlalchemy.String)
    command_type = sqlalchemy.Column(sqlalchemy.String)
    raw = sqlalchemy.Column(sqlalchemy.String)
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=func.now())

    user: DiscordUser = relationship("DiscordUser", backref="logs")

    def save(self, *args, **kwargs):
        user, created = DiscordUser.get_or_create(
            defaults={"created_at": self.created_at}, id=self.user_id
        )

        if not created:
            user.last_used_at = self.created_at
        return super().save(*args, **kwargs)

    def __repr__(self) -> str:
        return f"<DiscordBotRequestLog object {self.id}>"


class DiscordBotCommandEventLog(Base):
    __tablename__ = "discord_bot_command_event_logs"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    request_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey(DiscordBotRequestLog.id)
    )
    event = sqlalchemy.Column(sqlalchemy.String)
    properties = sqlalchemy.Column(sqlalchemy.String)
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=func.now())

    request: DiscordBotRequestLog = relationship(
        "DiscordBotRequestLog", backref="events"
    )

    def __repr__(self) -> str:
        return f"<DiscordBotCommandEventLog object {self.id}>"
