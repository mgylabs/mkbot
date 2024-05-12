import itertools
from datetime import datetime, timezone

from sqlalchemy.orm import joinedload

from mgylabs.db import database
from mgylabs.db.models import DiscordBotCommandEventLog, DiscordBotRequestLog
from mgylabs.db.storage import localStorage
from mgylabs.services.telemetry_service import TelemetryReporter


def row2dict(r, excepts=[]):
    return {
        c.name: getattr(r, c.name) for c in r.__table__.columns if c.name not in excepts
    }


def gen(r, ev=True):
    d = row2dict(r)
    d.pop("user_id")
    d["user"] = row2dict(r.user)
    if ev:
        d["events"] = [row2dict(e, ["request_id"]) for e in r.events]
    else:
        d["events_count"] = len(r.events)

    return d


def gen2(r):
    d = row2dict(r)
    d.pop("request_id")
    d["request"] = gen(r.request, False)

    return d


def group_by(d, k):
    return [(sk, [t[1] for t in g]) for sk, g in itertools.groupby(d, k)]


@database.using_database
def usage_helper():
    last_log_id = localStorage["telemetry_last_log_id"]
    last_at = localStorage["telemetry_last_at"]

    if last_log_id is None:
        last_log_id = 0

    if last_at is None:
        last_at = datetime.now(timezone.utc).replace(tzinfo=None)

    current_time = datetime.now(timezone.utc).replace(tzinfo=None)

    out = (
        DiscordBotRequestLog.query.filter(
            DiscordBotRequestLog.id > last_log_id,
            current_time >= DiscordBotRequestLog.created_at,
        )
        .order_by(DiscordBotRequestLog.created_at)
        .options(
            joinedload(DiscordBotRequestLog.user),
            joinedload(DiscordBotRequestLog.events),
        )
        .all()
    )

    up = (
        DiscordBotCommandEventLog.query.filter(
            last_log_id >= DiscordBotCommandEventLog.request_id,
            current_time >= DiscordBotCommandEventLog.created_at,
            DiscordBotCommandEventLog.created_at > last_at,
        )
        .order_by(DiscordBotCommandEventLog.created_at)
        .options(
            joinedload(DiscordBotCommandEventLog.request).joinedload(
                DiscordBotRequestLog.user
            ),
            joinedload(DiscordBotCommandEventLog.request).joinedload(
                DiscordBotRequestLog.events
            ),
        )
        .all()
    )

    if len(out) or len(up):

        @database.using_database
        def callback():
            if len(out):
                localStorage["telemetry_last_log_id"] = out[-1].id
            localStorage["telemetry_last_at"] = current_time

        TelemetryReporter.Event(
            "Usage",
            {"data": {"request": list(map(gen, out)), "update": list(map(gen2, up))}},
            callback,
        )
