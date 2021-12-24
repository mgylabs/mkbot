from mgylabs.db.models import DiscordBotLog
from mgylabs.db.storage import localStorage
from mgylabs.services.telemetry_service import TelemetryReporter
from sqlalchemy.orm import joinedload


def row2dict(r):
    return {c.name: str(getattr(r, c.name)) for c in r.__table__.columns}


def gen(r):
    d = row2dict(r)
    d.pop("user_id")
    d["user"] = row2dict(r.user)

    return d


def usage_helper():
    last_log_id = localStorage["telemetry_last_log_id"]

    if last_log_id is None:
        last_log_id = 0

    out = (
        DiscordBotLog.query()
        .filter(DiscordBotLog.id > last_log_id)
        .order_by(DiscordBotLog.created_at)
        .options(joinedload(DiscordBotLog.user))
        .limit(100)
        .all()
    )

    if len(out):
        TelemetryReporter.send_telemetry_event("Usage", {"data": list(map(gen, out))})

        localStorage["telemetry_last_log_id"] = len(out) + last_log_id
