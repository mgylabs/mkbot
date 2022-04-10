from mgylabs.db.models import DiscordBotRequestLog
from mgylabs.db.storage import localStorage
from mgylabs.services.telemetry_service import TelemetryReporter
from sqlalchemy.orm import joinedload


def row2dict(r, excepts=[]):
    return {
        c.name: str(getattr(r, c.name))
        for c in r.__table__.columns
        if c.name not in excepts
    }


def gen(r):
    d = row2dict(r)
    d.pop("user_id")
    d["user"] = row2dict(r.user)
    d["events"] = [row2dict(e, ["request_id"]) for e in r.events]

    return d


def usage_helper():
    last_log_id = localStorage["telemetry_last_log_id"]

    if last_log_id is None:
        last_log_id = 0

    out = (
        DiscordBotRequestLog.query()
        .filter(DiscordBotRequestLog.id > last_log_id)
        .order_by(DiscordBotRequestLog.created_at)
        .options(joinedload(DiscordBotRequestLog.user))
        .options(joinedload(DiscordBotRequestLog.events))
        .all()
    )

    if len(out):

        def callback():
            localStorage["telemetry_last_log_id"] = len(out) + last_log_id

        TelemetryReporter.Event("Usage", {"data": list(map(gen, out))}, callback)
