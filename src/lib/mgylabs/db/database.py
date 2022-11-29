import logging
import os
import sys

from alembic import command
from alembic.config import Config
from mgylabs.utils import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker
from sqlalchemy.orm.decl_api import DeclarativeMeta

from .paths import DB_URL

log = logger.get_logger(__name__)

engine = create_engine(DB_URL, echo=False)

db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

Base: DeclarativeMeta = declarative_base()
Base.query = db_session.query_property()


def is_development_mode():
    return not getattr(sys, "frozen", False)


def write_flag():
    if not is_development_mode():
        with open("migration.flag", "wt") as f:
            f.write("flag")


def exist_flag():
    return False if is_development_mode() else os.path.isfile("migration.flag")


def run_migrations(script_location: str, dsn: str) -> None:
    if not exist_flag():
        log.info("Running DB migrations in %r on %r", script_location, dsn)
        alembic_cfg = Config()
        alembic_cfg.set_main_option("script_location", script_location)
        alembic_cfg.set_main_option("sqlalchemy.url", dsn)
        command.upgrade(alembic_cfg, "head")

        write_flag()


def init_db():
    from mgylabs.db import models

    Base.metadata.create_all(engine)
