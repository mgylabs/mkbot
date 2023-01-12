from __future__ import annotations

import contextvars
import inspect
import os
import sys
import threading
from contextlib import contextmanager
from functools import wraps
from typing import List, Type, TypeVar

import sqlalchemy.orm
import sqlalchemy.util
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as ORMSession
from sqlalchemy.orm import declarative_base, object_session, scoped_session

from mgylabs.utils import logger

from .paths import DB_URL, USER_DATA_PATH

log = logger.get_logger(__name__)

Session: scoped_session = None


def needs_db_session(func):
    @wraps(func)
    def checker(self, **kwargs):
        session: DataBaseSession = object_session(self)
        if session and session == self._session:
            return func(self, **kwargs)
        else:
            raise Exception("There is no attached sessions.")

    return checker


class ContextSession:
    # @classmethod
    # def hook_del(cls, instance):
    #     if session := cls._session.get(None):
    #         objects = list(session.identity_map.values())
    #         if len(objects) == 0 or (len(objects) == 1 and instance in objects):
    #             cls._session.set(None)
    #             session.close()
    #             Session.remove()

    def __get__(self, instance, cls) -> DataBaseSession:
        return Session()

    def __set__(self, instance, value):
        pass


class ContextQuery:
    def __get__(self, instance, cls) -> Query:
        return cls._session.query(cls)

    def __set__(self, instance, value):
        pass


M = TypeVar("M", bound="CRUDBase")


class CRUDBase:
    _session = ContextSession()
    query = ContextQuery()

    def __init__(self, **kwargs) -> None:
        for attr, value in kwargs.items():
            setattr(self, attr, value)

    @classmethod
    def count(cls, **kwargs):
        return cls.query.filter_by(**kwargs).count()

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        instance.save()
        return instance

    def save(self, *args, **kwargs):
        if not kwargs.get("in_event", False):
            self._session.add(self)
            if not self._session.get_nested_transaction():
                self._session.commit()
        return self

    @needs_db_session
    def update(self, **kwargs):
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        self.save()
        return self

    @needs_db_session
    def delete(self):
        self._session.delete(self)
        if not self._session.get_nested_transaction():
            self._session.commit()
        return self

    @classmethod
    def get(cls: Type[M], **kwargs) -> List[M]:
        return cls.query.filter_by(**kwargs).all()

    @classmethod
    def get_one(cls: Type[M], **kwargs) -> M:
        return cls.query.filter_by(**kwargs).one()

    @classmethod
    def get_one_or_none(cls: Type[M], **kwargs) -> M:
        return cls.query.filter_by(**kwargs).one_or_none()

    @classmethod
    def get_or_create(cls, defaults={}, **kwargs):
        instance = cls.get_one_or_none(**kwargs)

        if instance:
            return instance, False
        else:
            try:
                with cls._session.begin_nested():
                    instance: CRUDBase = cls.create(**kwargs, **defaults)
                return instance, True
            except IntegrityError:
                return cls.get_one(**kwargs), False

    @classmethod
    def update_or_create(cls, defaults={}, **kwargs):
        instance, created = cls.get_or_create(defaults, **kwargs)
        if created:
            return instance, created
        else:
            instance.update(**defaults)
            return instance, False

    @classmethod
    def __declare_last__(cls):
        event.listen(cls, "before_update", receive_before_insert_or_update)


def receive_before_insert_or_update(mapper, connection, target: CRUDBase):
    target.save(in_event=True)


class Query(sqlalchemy.orm.Query):
    def __init__(self, entities, session) -> None:
        super().__init__(entities, session)
        self.session: DataBaseSession
        self.ModelClass = None
        if model_class := sqlalchemy.util.to_list(entities):
            if len(model_class):
                self.ModelClass = model_class[0]


class DataBaseSession(ORMSession):
    def query(self, *entities, **kwargs) -> Query:
        return super().query(*entities, **kwargs)


class sessionmaker(sqlalchemy.orm.sessionmaker):
    def __call__(self, **local_kw) -> DataBaseSession:
        return super().__call__(**local_kw)


class ScopeManager:
    def __init__(self) -> None:
        self._session_id = contextvars.ContextVar("_session_id")
        self.lock = threading.Lock()
        self.last_id = 0

    def get_session_id(self):
        return self._session_id.get(None)

    def set_session_id(self):
        with self.lock:
            self.last_id += 1
            return self._session_id.set(self.last_id)

    def reset_session_id(self, token):
        self._session_id.reset(token)

    def __call__(self, *args, **kwds):
        return self._session_id.get()


scope_manager = ScopeManager()


class EngineManager:
    engine = None

    @classmethod
    def set_engine_url(cls, url=DB_URL, echo=False):
        global Session
        cls.engine = create_engine(DB_URL, echo=echo)
        Session = scoped_session(
            sessionmaker(
                autocommit=False,
                autoflush=True,
                bind=cls.engine,
                class_=DataBaseSession,
                query_cls=Query,
                expire_on_commit=False,
            ),
            scopefunc=scope_manager,
        )

    @classmethod
    def dispose_engine(cls):
        cls.engine.dispose()


Base: Type[CRUDBase] = declarative_base(cls=CRUDBase)
# Base.query = db_session.query_property()


@contextmanager
def db_session():
    id_token = scope_manager.set_session_id()
    session: DataBaseSession = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        Session.remove()
        scope_manager.reset_session_id(id_token)


@contextmanager
def transaction():
    session: DataBaseSession = Session()

    with session.begin_nested():
        yield session


def using_database(func):
    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def wrapped(*args, **kwargs):
            with db_session():
                return await func(*args, **kwargs)

    else:

        @wraps(func)
        def wrapped(*args, **kwargs):
            with db_session():
                return func(*args, **kwargs)

    return wrapped


def is_development_mode():
    return not getattr(sys, "frozen", False)


def write_flag():
    if not is_development_mode():
        with open("migration.flag", "wt") as f:
            f.write("flag")


def exist_flag():
    return False if is_development_mode() else os.path.isfile("migration.flag")


def run_migrations(script_location: str, dsn: str, url=DB_URL, echo=False) -> None:
    EngineManager.set_engine_url(url, echo)

    if not exist_flag():
        log.info("Running DB migrations in %r on %r", script_location, dsn)
        os.makedirs(USER_DATA_PATH, exist_ok=True)
        alembic_cfg = Config()
        alembic_cfg.set_main_option("script_location", script_location)
        alembic_cfg.set_main_option("sqlalchemy.url", dsn)
        command.upgrade(alembic_cfg, "head")

        write_flag()


def init_db():
    from mgylabs.db import models

    Base.metadata.create_all(EngineManager.engine)


def drop_db():
    from mgylabs.db import models

    Base.metadata.drop_all(EngineManager.engine)


def run_downgrade_base(script_location: str, dsn: str):
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", script_location)
    alembic_cfg.set_main_option("sqlalchemy.url", dsn)
    command.downgrade(alembic_cfg, "base")
