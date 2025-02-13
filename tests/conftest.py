import asyncio
import builtins
import io
import os

import pytest

from mgylabs.db.database import db_session, run_downgrade_base, run_migrations
from mgylabs.db.paths import DB_FILE, DB_URL, SCRIPT_DIR
from mgylabs.utils.event import AsyncScheduler


@pytest.fixture
def new_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


def patch_open(open_func, files):
    def open_patched(
        path,
        mode="r",
        buffering=-1,
        encoding=None,
        errors=None,
        newline=None,
        closefd=True,
        opener=None,
    ):
        if "w" in mode and not os.path.isfile(path):
            files.append(path)
        return open_func(
            path,
            mode=mode,
            buffering=buffering,
            encoding=encoding,
            errors=errors,
            newline=newline,
            closefd=closefd,
            opener=opener,
        )

    return open_patched


@pytest.fixture(autouse=True)
def cleanup_files(monkeypatch):
    files = []
    monkeypatch.setattr(builtins, "open", patch_open(builtins.open, files))
    monkeypatch.setattr(io, "open", patch_open(io.open, files))
    yield
    for file in files:
        print("Remove", file)
        if os.path.isfile(file):
            os.remove(file)


@pytest.fixture(scope="session")
def cleanup_database():
    if os.path.isfile(DB_FILE):
        os.remove(DB_FILE)
    yield
    if os.path.isfile(DB_FILE):
        os.remove(DB_FILE)


@pytest.fixture()
def needs_database(cleanup_database):
    run_migrations(SCRIPT_DIR, DB_URL)
    with db_session():
        yield
    run_downgrade_base(SCRIPT_DIR, DB_URL)


@pytest.fixture()
def needs_database_without_session(cleanup_database):
    run_migrations(SCRIPT_DIR, DB_URL)
    yield
    run_downgrade_base(SCRIPT_DIR, DB_URL)


@pytest.fixture()
async def needs_async_scheduler():
    yield
    await AsyncScheduler.terminate()
