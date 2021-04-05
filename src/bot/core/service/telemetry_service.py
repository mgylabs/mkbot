import traceback

from ..utils.config import DISCRIMINATOR, VERSION, is_development_mode

try:
    # pylint: disable=import-error,no-name-in-module

    from mulgyeol_telemetry.telemetry import TelemetryClient

    from ..utils.APIKey import INSIGHTS_APPLICATION_KEY

    # pylint: disable=import-error,no-name-in-module
except ModuleNotFoundError:
    telemetry_enabled = False
except Exception:
    telemetry_enabled = False
    traceback.print_exc()
else:
    telemetry_enabled = True


class TelemetryService:
    reporter = None

    @classmethod
    def send_telemetry_event(cls, event_name, properties={}):
        if cls.reporter is not None:
            return cls.reporter.send_telemetry_event(event_name, properties)

    @classmethod
    def start(cls):
        if telemetry_enabled and not is_development_mode() and cls.reporter is None:
            cls.reporter = TelemetryClient(
                INSIGHTS_APPLICATION_KEY, str(VERSION), DISCRIMINATOR
            )

        cls.send_telemetry_event("login")
