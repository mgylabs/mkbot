import hashlib
import json
import msvcrt  # pylint: disable=import-error
import os
import subprocess
import sys
import traceback
import zipfile

import requests
from packaging import version
from requests.sessions import HTTPAdapter

sys.path.append("..\\lib")

from mgylabs.services.telemetry_service import TelemetryReporter


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


class VersionInfo:
    def __init__(self, label, url):
        _, self.rtype, self.version, self.sha = label.split("-")
        self.commit = None
        self.url = url
        if self.rtype.lower() == "canary":
            self.commit = self.version.split(".")[-1]
            self.version = self.version.replace(f".{self.commit}", "")
            self.version = version.parse(self.version + "-beta")
        else:
            self.version = version.parse(self.version)


def is_canary_release(version_str: str):
    version_str = version_str.split("-")
    return True if (len(version_str) > 1 and version_str[1] == "beta") else False


class BaseUpdater:
    def __init__(
        self,
        current_data,
        download_dir_name="mkbot_update",
        setup_name="MKBotSetup.exe",
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
        self.setup_path = self.download_dir_path + f"\\{setup_name}"

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

    @classmethod
    def find_asset(self, assets):
        asset = None
        for d in assets:
            if d["label"].lower().startswith("mkbotsetup-"):
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
            subprocess.call([self.setup_path, "/S", "/unpack"])
        else:
            download_file_name = f"{self.download_dir_path}\\MKBotSetup.zip"

            os.makedirs(os.path.dirname(download_file_name), exist_ok=True)

            self.download_file(download_file_name)

            _zip = zipfile.ZipFile(download_file_name)
            _zip.extractall(self.download_dir_path)

            if self.check_sha1_hash():
                subprocess.call([self.setup_path, "/S", "/unpack"])

    def check_sha1_hash(self):
        if os.path.isfile(self.setup_path):
            with open(self.setup_path, "rb") as f:
                file_data = f.read()
            return hashlib.sha1(file_data).hexdigest() == self.target.sha
        else:
            return False

    @staticmethod
    def check_ready_to_update():
        return os.path.isfile("../Update.flag") and os.path.isdir("../_")

    def run(self):
        if self.check_ready_to_update():
            sys.exit(0)
        self.check_new_update()
        self.download()
        if self.check_ready_to_update():
            sys.exit(0)
        else:
            sys.exit(1)

    @classmethod
    def can_install(cls):
        if cls.check_ready_to_update():
            sys.exit(0)
        else:
            sys.exit(1)


class StableUpdater(BaseUpdater):
    def __init__(self, current_data):
        super().__init__(current_data, beta=False)

    def request_stable_update(self):
        return self.session.get(
            "https://api.github.com/repos/mgylabs/mulgyeol-mkbot/releases/latest"
        )


class CanaryUpdater(BaseUpdater):
    def __init__(self, current_data):
        super().__init__(current_data, beta=False)

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

    if "/s" in sys.argv:
        Updater.can_install()
    elif "/c" in sys.argv:
        Updater.run()
    else:
        sys.exit(1)


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
