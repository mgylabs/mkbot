import hashlib
import json
import msvcrt  # pylint: disable=import-error
import os
import pathlib
import shutil
import subprocess
import sys
import zipfile

import requests
from packaging import version
from requests.sessions import HTTPAdapter

sys.path.append("..\\lib")

from mgylabs.services.telemetry_service import TelemetryReporter
from mgylabs.utils.logger import get_logger

log = get_logger(__name__)


def is_development_mode():
    return not getattr(sys, "frozen", False)


def write_flag():
    with open("msu.flag", "wt") as f:
        f.write("flag")


def exist_flag():
    return os.path.isfile("msu.flag")


def instance_already_running(canary_build):
    if canary_build:
        lock_name = "mkbot_can_msu.lock"
    else:
        lock_name = "mkbot_msu.lock"

    fd = os.open(f"{os.getenv('TEMP')}\\{lock_name}", os.O_WRONLY | os.O_CREAT)

    try:
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        already_running = False
    except IOError:
        already_running = True

    return already_running


def write_update_flag(text):
    with open("msu_update.flag", "wt") as f:
        f.write(text)


class VersionInfo:
    def __init__(self, label, url):
        _, self.rtype, self.base_version, self.sha = label.split("-")
        self.commit = None
        self.url = url
        if self.rtype.lower() == "canary":
            self.commit = self.base_version.split(".")[-1]
            self.base_version = self.base_version.replace(f".{self.commit}", "")
            self.version_str = f"{self.base_version}.{self.commit[:7]}"
            self.version = version.parse(self.base_version + "-beta")
        else:
            self.version = version.parse(self.base_version)
            self.version_str = self.base_version


def is_canary_release(version_str: str):
    version_str = version_str.split("-")
    return True if (len(version_str) > 1 and version_str[1] == "beta") else False


class BaseUpdater:
    def __init__(
        self,
        current_data,
        download_dir_name="mkbot-update",
        setup_base_name="MKBotSetup",
        beta=False,
    ):
        self.enabled_beta = beta

        self.current_data = current_data
        self.current_version = version.parse(current_data["version"])

        self.last_beta = None
        self.target = None

        self.session = requests.Session()
        self.session.mount("https://", HTTPAdapter(max_retries=3))

        self.download_dir_path = os.getenv("TEMP") + f"\\{download_dir_name}"
        self.setup_base_name = setup_base_name

    def get_version_info(self, res):
        res.raise_for_status()
        data = res.json()
        asset = self.find_asset(data["assets"])

        if asset == None:
            return None

        return VersionInfo(asset["label"], asset["browser_download_url"])

    def request_stable_update(self):
        return self.session.get(
            "https://api.github.com/repos/mgylabs/mulgyeol-mkbot/releases/latest"
        )

    def request_beta_update(self):
        return self.session.get(
            "https://api.github.com/repos/mgylabs/mulgyeol-mkbot/releases/tags/canary"
        )

    def check_new_update(self):
        if self.current_data.get("commit", None) == None:
            sys.exit(1)

        if exist_flag():
            TelemetryReporter.Health()
        else:
            TelemetryReporter.Event("CheckedForUpdate")
            write_flag()

        self.last_stable = self.get_version_info(self.request_stable_update())

        if self.last_stable is None:
            sys.exit(1)

        if self.last_stable.version > self.current_version:
            self.target = self.last_stable
        elif self.enabled_beta:
            self.last_beta = self.get_version_info(self.request_beta_update())
            if (
                self.last_beta
                and self.last_beta.version > self.last_stable.version
                and self.last_beta.version >= self.current_version
                and self.last_beta.commit != self.current_data["commit"]
            ):
                self.target = self.last_beta
            else:
                sys.exit(1)
        else:
            sys.exit(1)

        base = (
            self.download_dir_path
            + f"\\{self.setup_base_name}-{self.target.version_str}"
        )
        self.setup_path = f"{base}.exe"
        self.flag_path = f"{base}.flag"

    def find_asset(self, assets):
        asset = None
        for d in assets:
            if d["label"].lower().startswith(f"{self.setup_base_name.lower()}-"):
                asset = d
                break

        return asset

    def download_file(self, download_file_name):
        with self.session.get(self.target.url, stream=True) as r:
            r.raise_for_status()

            with open(download_file_name, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)

        TelemetryReporter.Event(
            "UpdateDownloaded",
            {"status": r.status_code, "url": self.target.url},
        )

    def download(self):
        if self.check_sha1_hash():
            self.run_setup()
        else:
            download_file_name = f"{self.download_dir_path}\\{self.setup_base_name}.zip"

            if os.path.isdir(os.path.dirname(download_file_name)):
                shutil.rmtree(os.path.dirname(download_file_name), ignore_errors=True)

            os.makedirs(os.path.dirname(download_file_name), exist_ok=True)

            self.download_file(download_file_name)

            _zip = zipfile.ZipFile(download_file_name)
            _zip.extractall(self.download_dir_path)

            if self.check_sha1_hash():
                self.run_setup()
            else:
                sys.exit(1)

    def run_setup(self):
        self.create_flag()
        args = [
            self.setup_path,
            "/verysilent",
            f"/update={self.flag_path}",
            "/nocloseapplications",
            "/mergetasks=runapp,!desktopicon",
            "/gui=false",
        ]

        subprocess.Popen(args, cwd=pathlib.Path(__file__).parent.parent.resolve())

    def create_flag(self):
        with open(self.flag_path, "wt") as f:
            f.write("flag")

        write_update_flag(self.flag_path)

    def check_sha1_hash(self):
        if os.path.isfile(self.setup_path):
            with open(self.setup_path, "rb") as f:
                file_data = f.read()
            return hashlib.sha1(file_data).hexdigest() == self.target.sha
        else:
            return False

    def run(self):
        self.check_new_update()
        self.download()
        sys.exit(0)


class StableUpdater(BaseUpdater):
    def __init__(self, current_data):
        super().__init__(current_data, beta=False)

    def request_stable_update(self):
        return self.session.get(
            "https://api.github.com/repos/mgylabs/mulgyeol-mkbot/releases/latest"
        )


class CanaryUpdater(BaseUpdater):
    def __init__(self, current_data):
        super().__init__(
            current_data, beta=False, download_dir_name="mkbot-canary-update"
        )

    def request_stable_update(self):
        return self.session.get(
            "https://api.github.com/repos/mgylabs/mulgyeol-mkbot/releases/tags/canary"
        )


def main():
    with open("../info/version.json", "rt") as f:
        current_data = json.load(f)

    canary_build = is_canary_release(current_data["version"])

    if instance_already_running(canary_build):
        sys.exit(1)

    if canary_build:
        Updater = CanaryUpdater(current_data)
    else:
        Updater = StableUpdater(current_data)

    if "/c" in sys.argv:
        Updater.run()
    else:
        sys.exit(1)


if __name__ == "__main__":
    with TelemetryReporter():
        try:
            main()
        except Exception as error:
            TelemetryReporter.Exception(error)
            log.error(error, exc_info=True)
            sys.exit(1)
