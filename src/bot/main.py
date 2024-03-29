from multiprocessing import freeze_support

freeze_support()

import sys

sys.path.append("../lib")
from mgylabs.utils import logger

logger.configure_logger()

import asyncio
import msvcrt
import os

from core.controllers.ipc_controller import IPCController
from discord_host import create_bot, start_bot
from mgylabs.db.database import run_migrations
from mgylabs.db.paths import DB_URL, SCRIPT_DIR
from mgylabs.services.telemetry_service import TelemetryReporter
from mgylabs.utils import logger
from mgylabs.utils.version import VERSION

os.chdir(os.path.dirname(os.path.abspath(__file__)))

log = logger.get_logger(__name__)


def instance_already_running():
    if VERSION.is_canary():
        if "--schtasks" in sys.argv:
            lock_name = "mkbot_can_sch.lock"
        else:
            lock_name = "mkbot_can.lock"
    else:
        if "--schtasks" in sys.argv:
            lock_name = "mkbot_sch.lock"
        else:
            lock_name = "mkbot.lock"

    fd = os.open(f"{os.getenv('TEMP')}\\{lock_name}", os.O_WRONLY | os.O_CREAT)

    try:
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        already_running = False
    except IOError:
        already_running = True

    return already_running


async def dry_run():
    errorlevel = await create_bot(True)
    return errorlevel


def main():
    if instance_already_running():
        print("MKBotCore is already running.")
        sys.exit(0)

    run_migrations(SCRIPT_DIR, DB_URL)

    if "--test-bot" in sys.argv:
        asyncio.run(start_bot())
        sys.exit()

    if "--dry-run" in sys.argv:
        errorlevel = asyncio.run(dry_run())
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
    with TelemetryReporter():
        try:
            main()
        except Exception as error:
            TelemetryReporter.Exception(error)
            log.error(error, exc_info=True)
            sys.exit(1)
