import logging
import sys

from discord_host import create_bot

sys.path.append("..\\lib")
import msvcrt
import os
import traceback

from mgylabs.db.database import run_migrations
from mgylabs.db.paths import DB_URL, SCRIPT_DIR
from mgylabs.services.telemetry_service import TelemetryReporter

from core.controllers.ipc_controller import IPCController

os.chdir(os.path.dirname(os.path.abspath(__file__)))

log = logging.getLogger(__name__)


def instance_already_running():
    fd = os.open(f"{os.getenv('TEMP')}\\mkbot.lock", os.O_WRONLY | os.O_CREAT)

    try:
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        already_running = False
    except IOError:
        already_running = True

    return already_running


def main():
    if instance_already_running():
        print("MKBotCore is already running.")
        sys.exit(0)

    run_migrations(SCRIPT_DIR, DB_URL)

    if "--dry-run" in sys.argv:
        errorlevel = create_bot(True)
        if errorlevel == 0:
            print("Test Passed")
        else:
            print("Test Failed")
        sys.exit(errorlevel)

    if "--port" in sys.argv:
        try:
            loc = sys.argv.index("--port")
            PORT = int(sys.argv[loc + 1])
        except Exception:
            PORT = 8979
    else:
        PORT = 8979

    ipc_controller = IPCController(PORT)
    ipc_controller.run()


if __name__ == "__main__":
    error = 0

    try:
        TelemetryReporter.start()
        main()
    except SystemExit as e:
        error = e.code
    except Exception as e:
        TelemetryReporter.Exception(e)
        traceback.print_exc()
        error = 1
    finally:
        TelemetryReporter.terminate()
        sys.exit(error)
