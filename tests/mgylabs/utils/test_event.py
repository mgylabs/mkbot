import asyncio
from datetime import datetime, timedelta

from mgylabs.utils.event import AsyncScheduler, SchTask


async def test_AsyncScheduler():
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
