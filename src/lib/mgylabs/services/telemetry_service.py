import platform
import traceback

from ..utils.config import DISCRIMINATOR, VERSION

try:
    # pylint: disable=import-error,no-name-in-module

    from mulgyeol_telemetry.telemetry import TelemetryClient

    from ..constants.APIKey import INSIGHTS_APPLICATION_KEY

    # pylint: disable=import-error,no-name-in-module
except ModuleNotFoundError:
    telemetry_enabled = False
except Exception:
    telemetry_enabled = False
    traceback.print_exc()
else:
    telemetry_enabled = True


class TelemetryReporter:
    reporter = None

    @classmethod
    def send_telemetry_event(cls, event_name, properties={}):
        properties["commit"] = VERSION.commit
        properties["OS"] = platform.platform().replace("-", " ")

        if cls.reporter is not None:
            return cls.reporter.send_telemetry_event(event_name, properties)

    @classmethod
    def send_telemetry_exception(cls, error, properties={}):
        assert isinstance(error, Exception)

        properties["commit"] = VERSION.commit
        properties["OS"] = platform.platform().replace("-", " ")

        if cls.reporter is not None:
            return cls.reporter.send_telemetry_exception(error, properties)

    @classmethod
    def start(cls, callback_event_name=None):
        if telemetry_enabled and VERSION.is_release_build() and cls.reporter is None:
            cls.reporter = TelemetryClient(
                INSIGHTS_APPLICATION_KEY, str(VERSION), DISCRIMINATOR
            )

        if callback_event_name is not None:
            cls.send_telemetry_event(str(callback_event_name))
