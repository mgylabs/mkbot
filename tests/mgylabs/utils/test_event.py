import asyncio
from datetime import datetime, timedelta

from mgylabs.utils.event import AsyncScheduler, SchTask


async def test_AsyncScheduler_single_task():
    for _ in range(2):
        task_result: datetime = None
        pending = asyncio.Event()

        async def simple_task():
            nonlocal task_result

            task_result = datetime.now()
            pending.set()

        start = datetime.now()

        await AsyncScheduler.add_task(
            SchTask(start + timedelta(seconds=3), simple_task())
        )

        await pending.wait()

        diff = (task_result - start).total_seconds()

        print(diff)
        assert diff >= 3
        assert AsyncScheduler.pending.is_set() is False


async def test_AsyncScheduler_multiple_task():
    task_result: dict[int, datetime] = {}
    pending = [asyncio.Event(), asyncio.Event()]

    async def simple_task(i):
        task_result[i] = datetime.now()
        pending[i].set()

    start = datetime.now()

    await AsyncScheduler.add_task(SchTask(start + timedelta(seconds=5), simple_task(1)))
    await AsyncScheduler.add_task(SchTask(start + timedelta(seconds=3), simple_task(0)))

    for p in pending:
        await p.wait()

    diff = [(t - start).total_seconds() for t in task_result.values()]

    print(diff)
    assert diff[0] >= 3
    assert diff[1] >= 5
    assert diff[1] > diff[0]
    assert AsyncScheduler.pending.is_set() is False
