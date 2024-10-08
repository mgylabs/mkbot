import platform
import threading
import traceback

from ..utils.config import VERSION

try:
    # pylint: disable=import-error,no-name-in-module

    from mulgyeol_telemetry.telemetry import TelemetryClient  # type: ignore @IgnoreException isort:skip
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

    def __enter__(self, callback_event_name=None):
        TelemetryReporter.start(callback_event_name)
        return self

    def __exit__(self, type, value, traceback):
        TelemetryReporter.terminate()

    @classmethod
    def _run_callback_(cls, callback):
        if callback is not None:
            threading.Thread(target=callback).start()

    @classmethod
    def Health(cls, callback=None):
        if cls.reporter is not None:
            return cls.reporter.Health(callback)
        else:
            cls._run_callback_(callback)

    @classmethod
    def Event(cls, event_name, properties={}, callback=None):
        properties["commit"] = VERSION.commit
        properties["OS"] = platform.platform().replace("-", " ")

        if cls.reporter is not None:
            return cls.reporter.Event(event_name, properties, callback)
        else:
            cls._run_callback_(callback)

    @classmethod
    def Exception(cls, error, properties={}, callback=None):
        assert isinstance(error, Exception)

        properties["commit"] = VERSION.commit
        properties["OS"] = platform.platform().replace("-", " ")

        if cls.reporter is not None:
            return cls.reporter.Exception(error, properties, callback)
        else:
            cls._run_callback_(callback)

    @classmethod
    def start(cls, callback_event_name=None, properties={}):
        if telemetry_enabled and VERSION.is_release_build() and cls.reporter is None:
            cls.reporter = TelemetryClient(INSIGHTS_APPLICATION_KEY, str(VERSION))

        if callback_event_name is not None:
            cls.Event(str(callback_event_name), properties)

    @classmethod
    def terminate(cls):
        if cls.reporter is not None:
            cls.reporter.terminate()
