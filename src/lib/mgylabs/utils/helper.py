import itertools

from sqlalchemy.orm import joinedload

from mgylabs.db import database
from mgylabs.db.models import DiscordBotCommandEventLog, DiscordBotRequestLog
from mgylabs.db.storage import localStorage
from mgylabs.services.telemetry_service import TelemetryReporter


def row2dict(r, excepts=[]):
    return {
        c.name: getattr(r, c.name) for c in r.__table__.columns if c.name not in excepts
    }


def gen(r):
    d = row2dict(r)
    d.pop("user_id")
    d["user"] = row2dict(r.user)
    d["events"] = [row2dict(e, ["request_id"]) for e in r.events]

    return d


def group_by(d, k):
    return [(sk, [t[1] for t in g]) for sk, g in itertools.groupby(d, k)]


@database.using_database
def usage_helper():
    last_log_id = localStorage["telemetry_last_log_id"]

    if last_log_id is None:
        last_log_id = 0

    out = (
        DiscordBotRequestLog.query.filter(DiscordBotRequestLog.id > last_log_id)
        .order_by(DiscordBotRequestLog.created_at)
        .options(joinedload(DiscordBotRequestLog.user))
        .options(joinedload(DiscordBotRequestLog.events))
        .all()
    )

    up = (
        DiscordBotRequestLog.query.filter(
            DiscordBotRequestLog.id
            == DiscordBotCommandEventLog.query.with_entities(
                DiscordBotCommandEventLog.request_id
            )
            .filter(
                DiscordBotCommandEventLog.created_at
                >= DiscordBotRequestLog.query.with_entities(
                    DiscordBotRequestLog.created_at
                )
                .filter_by(id=last_log_id)
                .subquery()
                .c.created_at
            )
            .subquery()
            .c.request_id
        )
        .options(
            joinedload(DiscordBotRequestLog.user),
            joinedload(DiscordBotRequestLog.events),
        )
        .all()
    )

    if len(out) or len(up):

        @database.using_database
        def callback():
            localStorage["telemetry_last_log_id"] = len(out) + last_log_id

        TelemetryReporter.Event(
            "Usage",
            {"data": {"request": list(map(gen, out)), "update": list(map(gen, up))}},
            callback,
        )
