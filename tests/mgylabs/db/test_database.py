import asyncio

import pytest
from pytest_mock import MockerFixture
from sqlalchemy.exc import IntegrityError

from mgylabs.db import database
from mgylabs.db.models import DiscordUser


def test_create_discord_user(needs_database):
    user = DiscordUser.create(id=1)
    user = DiscordUser.get_one(id=1)

    assert user.id == 1
    assert user.created_at is not None
    assert user.timezone == "UTC"
    assert user.locale is None
    assert user.last_used_at == user.created_at


def test_update_discord_user(needs_database):
    user = DiscordUser.create(id=1)
    user.locale = "en"
    user.save()

    user = DiscordUser.get_one(id=1)

    assert user.id == 1
    assert user.created_at is not None
    assert user.timezone == "UTC"
    assert user.locale == "en"
    assert user.last_used_at == user.created_at


def test_call_save_when_updating_a_model(needs_database, mocker: MockerFixture):
    user = DiscordUser.create(id=1)

    save_func = mocker.spy(user, "save")
    with database.transaction():
        user.locale = "en"

    save_func.assert_called_once_with(in_event=True)
    assert save_func.spy_return == user
    assert user.id == 1
    assert user.created_at is not None
    assert user.timezone == "UTC"
    assert user.locale == "en"
    assert user.last_used_at == user.created_at


def test_transaction(needs_database):
    user = DiscordUser.create(id=1)
    DiscordUser.create(id=2)

    with pytest.raises(IntegrityError):
        with database.transaction():
            user.locale = "en"
            user.save()
            DiscordUser.create(id=2, locale="ko")

    user2 = DiscordUser.get_one(id=1)
    assert user2.locale is None


def test_transaction_in_coroutine(needs_database_without_session, new_event_loop):
    async def foo1():
        with pytest.raises(IntegrityError):
            with database.db_session():
                with database.transaction():
                    DiscordUser.create(id=1, locale="foo1")
                    DiscordUser.create(id=2, locale="foo2")
                    await asyncio.sleep(1)

    async def foo2():
        with database.db_session():
            with database.transaction():
                DiscordUser.create(id=2, locale="foo2")
                DiscordUser.create(id=1, locale="foo2")

    async def main():
        tasks = [asyncio.create_task(f) for f in [foo1(), foo2()]]
        await asyncio.gather(*tasks)

    new_event_loop.run_until_complete(main())

    with database.db_session():
        user1 = DiscordUser.get_one(id=1)
        user2 = DiscordUser.get_one_or_none(id=2)

    assert user1.locale == "foo2"
    assert [user2.id, user2.locale] == [2, "foo2"]


def test_transaction_nested(needs_database):
    user = DiscordUser.create(id=1)
    DiscordUser.create(id=2)

    with database.transaction():
        user.locale = "en"
        with pytest.raises(IntegrityError):
            with database.transaction():
                user.timezone = "Asia/Seoul"
                DiscordUser.create(id=2, locale="ko")

    assert user.locale == "en"
    assert user.timezone == "UTC"

    user.locale = "ko"
    assert user.locale == "ko"


def test_using_database_decorator(needs_database_without_session):
    @database.using_database
    def foo():
        user = DiscordUser.create(id=1)
        DiscordUser.create(id=2)

        with database.transaction():
            user.locale = "en"
            with pytest.raises(IntegrityError):
                with database.transaction():
                    user.timezone = "Asia/Seoul"
                    DiscordUser.create(id=2, locale="ko")

        assert user.locale == "en"
        assert user.timezone == "UTC"

        user.locale = "ko"
        assert user.locale == "ko"

    foo()
    assert database.Session.registry.registry == {}
