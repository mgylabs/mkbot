import datetime

import sqlalchemy
from sqlalchemy.orm import relationship

from .database import Base, db_session


class CRUD:
    @classmethod
    def count(cls, **kwargs):
        return db_session.query(cls).filter_by(**kwargs).count()

    @classmethod
    def query(cls):
        return db_session.query(cls)

    @classmethod
    def session(cls):
        return db_session

    @classmethod
    def get(cls, **kwargs):
        return db_session.query(cls).filter_by(**kwargs)

    @classmethod
    def get_one(cls, **kwargs):
        return db_session.query(cls).filter_by(**kwargs).first()

    @classmethod
    def get_or_create(cls, commit=True, defaults={}, **kwargs):
        instance = db_session.query(cls).filter_by(**kwargs).first()
        if instance:
            return instance, False
        else:
            instance = cls(**kwargs, **defaults)
            instance.save(commit=commit)
            return instance, True

    @classmethod
    def update_or_create(cls, commit=True, defaults={}, **kwargs):
        instance, created = cls.get_or_create(commit=False, defaults=defaults, **kwargs)
        if created:
            instance.save(commit=commit)
            return instance, created
        else:
            instance.update(commit=commit, **defaults)
            return instance, False

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        return instance.save()

    def update(self, commit=True, **kwargs):
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        return self.save(commit=commit) or self

    def save(self, commit=True):
        db_session.add(self)
        if commit:
            db_session.commit()
        return self

    def delete(self, commit=True):
        db_session.delete(self)
        return commit and db_session.commit()


class HashStore(CRUD, Base):
    __tablename__ = "hash_store"

    key = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    value = sqlalchemy.Column(sqlalchemy.String)

    def __init__(self, key, value) -> None:
        super().__init__()
        self.key = key
        self.value = value


class DiscordUser(CRUD, Base):
    __tablename__ = "discord_users"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    last_used_at = sqlalchemy.Column(sqlalchemy.DateTime)
    created_at = sqlalchemy.Column(
        sqlalchemy.DateTime, default=datetime.datetime.utcnow()
    )

    def __init__(self, id, created_at=None) -> None:
        super().__init__()
        self.id = id
        if created_at is not None:
            self.created_at = created_at

    def save(self, commit=True):
        if self.last_used_at is None:
            self.last_used_at = self.created_at
        return super().save(commit=commit)


class DiscordBotLog(CRUD, Base):
    __tablename__ = "discord_bot_logs"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey(DiscordUser.id)
    )
    msg_id = sqlalchemy.Column(sqlalchemy.Integer, unique=True)
    user_perm = sqlalchemy.Column(sqlalchemy.Integer)
    command = sqlalchemy.Column(sqlalchemy.String)
    raw = sqlalchemy.Column(sqlalchemy.String)
    created_at = sqlalchemy.Column(
        sqlalchemy.DateTime, default=datetime.datetime.utcnow()
    )

    user: DiscordUser = relationship("DiscordUser", backref="logs")

    def __init__(self, user_id, msg_id, user_perm, command, raw, created_at) -> None:
        super().__init__()
        self.user_id = user_id
        self.msg_id = msg_id
        self.user_perm = user_perm
        self.command = command
        self.raw = raw
        self.created_at = created_at

    def save(self, commit=True):
        user, created = DiscordUser.get_or_create(
            commit=False, defaults={"created_at": self.created_at}, id=self.user_id
        )
        if not created:
            user.last_used_at = self.created_at
        return super().save(commit=commit)

    def __repr__(self) -> str:
        return f"<DiscordBotLog object {self.id}>"
