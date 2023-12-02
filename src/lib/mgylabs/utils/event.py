import asyncio
import itertools
from dataclasses import dataclass
from datetime import datetime
from heapq import heappop, heappush
from typing import Any

import pytz

from mgylabs.utils import logger

log = logger.get_logger(__name__)


class Sleeper:
    # "Group sleep calls allowing instant cancellation of all"

    def __init__(self):
        self.tasks = set()

    async def sleep(self, delay, result=True, cancelled_result=False):
        coro = asyncio.sleep(delay, result=result)
        task = asyncio.ensure_future(coro)
        self.tasks.add(task)
        try:
            return await task
        except asyncio.CancelledError:
            return cancelled_result
        finally:
            self.tasks.remove(task)

    def cancel_all_helper(self):
        # "Cancel all pending sleep tasks"
        cancelled = set()
        for task in self.tasks:
            if task.cancel():
                cancelled.add(task)
        return cancelled

    async def cancel_all(self):
        # "Coroutine cancelling tasks"
        cancelled = self.cancel_all_helper()
        if self.tasks:
            await asyncio.wait(self.tasks)
            self.tasks -= cancelled
        return len(cancelled)


@dataclass(eq=False)
class SchTask:
    date: datetime
    task: Any
    done = False


class AsyncScheduler:
    pq = []
    entry_finder = {}
    REMOVED = "<removed-task>"

    sleeper = Sleeper()
    worker_running = False
    counter = itertools.count()
    pending = asyncio.Event()

    @classmethod
    async def add_task(cls, task: SchTask, priority=0):
        if task in cls.entry_finder:
            cls.remove_task(task)
        count = next(cls.counter)
        entry = [priority, task.date, count, task]
        cls.entry_finder[task] = entry
        heappush(cls.pq, entry)

        await cls.update_woker()

    @classmethod
    def remove_task(cls, task):
        # 'Mark an existing task as REMOVED. Raise KeyError if not found.'
        entry = cls.entry_finder.pop(task)
        entry[-1] = cls.REMOVED

    @classmethod
    def pop_entry(cls) -> SchTask:
        # 'Remove and return the lowest priority task. Raise KeyError if empty.'
        while cls.pq:
            entry = heappop(cls.pq)
            if entry[-1] is not cls.REMOVED:
                return entry

        raise KeyError("pop from an empty priority queue")

    @classmethod
    def pop_task(cls) -> SchTask:
        # 'Remove and return the lowest priority task. Raise KeyError if empty.'
        while cls.pq:
            _, _, _, task = heappop(cls.pq)
            if task is not cls.REMOVED:
                del cls.entry_finder[task]
                return task

        raise KeyError("pop from an empty priority queue")

    @classmethod
    async def get_target_task(cls):
        while True:
            entry = cls.pop_entry()
            sch_task = entry[-1]

            wait_time = cls.calc_remaining_time(sch_task.date)

            if wait_time <= 0:
                return sch_task

            if await cls.sleeper.sleep(wait_time):
                del cls.entry_finder[sch_task]
                return sch_task

            heappush(cls.pq, entry)

    @classmethod
    async def update_woker(cls):
        if not cls.worker_running:
            cls.worker_running = True
            asyncio.create_task(cls.run())
        else:
            cls.pending.set()
            await cls.sleeper.cancel_all()

    @classmethod
    async def run(cls):
        while True:
            if cls.pq:
                cls.pending.clear()
            else:
                await cls.pending.wait()

            try:
                sch_task = await cls.get_target_task()
            except KeyError:
                continue

            asyncio.create_task(sch_task.task)

    @classmethod
    def calc_remaining_time(cls, date: datetime, now: datetime = None) -> float:
        date = date.astimezone(pytz.UTC)
        if now is None:
            now = datetime.now(pytz.UTC)
        remaining_time = date - now

        log.info(f"AsyncScheduler: Waiting until {remaining_time}")

        return remaining_time.total_seconds()
