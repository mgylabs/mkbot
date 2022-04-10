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


if is_development_mode():
    CONFIG_PATH = "..\\data\\config.json"
else:
    CONFIG_PATH = (
        f"{os.getenv('LOCALAPPDATA')}\\Mulgyeol\\Mulgyeol MK Bot\\data\\config.json"
    )


def load_canary_config():
    try:
        with open(CONFIG_PATH, "rt", encoding="utf-8") as f:
            TOKEN = json.load(f)
        return TOKEN["canaryUpdate"]
    except Exception:
        return False


def instance_already_running():
    fd = os.open(f"{os.getenv('TEMP')}\\mkbot_msu.lock", os.O_WRONLY | os.O_CREAT)

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


class Updater:
    def __init__(self, current_data, enabled_canary=False):
        self.enabled_canary = enabled_canary

        self.current_version = version.parse(current_data["version"])

        self.last_canary = None
        self.target = None

        if current_data.get("commit", None) == None:
            sys.exit(1)

        self.session = requests.Session()
        self.session.mount("https://", HTTPAdapter(max_retries=3))

        res = self.session.get(
            "https://api.github.com/repos/mgylabs/mulgyeol-mkbot/releases/latest"
        )

        res.raise_for_status()
        data = res.json()

        if not exist_flag():
            TelemetryReporter.Event("CheckedForUpdate")
            write_flag()

        asset = self.find_asset(data["assets"])

        if asset == None:
            sys.exit(1)

        self.setupPath = os.getenv("TEMP") + "\\mkbot-update\\MKBotSetup.exe"

        self.last_stable = VersionInfo(asset["label"], asset["browser_download_url"])
        if self.last_stable.version > self.current_version:
            self.target = self.last_stable
        elif self.enabled_canary:
            res = self.session.get(
                "https://api.github.com/repos/mgylabs/mulgyeol-mkbot/releases/tags/canary"
            )
            try:
                res.raise_for_status()
                asset = self.find_asset(res.json()["assets"])
                if asset != None:
                    self.last_canary = VersionInfo(
                        asset["label"], asset["browser_download_url"]
                    )
            except Exception:
                traceback.print_exc()
            if (
                self.last_canary
                and self.last_canary.version > self.last_stable.version
                and self.last_canary.version >= self.current_version
                and self.last_canary.commit != current_data["commit"]
            ):
                self.target = self.last_canary
            else:
                sys.exit(1)
        else:
            sys.exit(1)

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

            TelemetryReporter.Event(
                "UpdateDownloaded",
                {"status": r.status_code, "url": self.target.url},
            )

            with open(download_file_name, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)

    def download(self):
        DOWNLOAD_PATH = f"{os.getenv('TEMP')}\\mkbot-update"
        if self.check_sha1_hash():
            subprocess.call([f"{DOWNLOAD_PATH}\\MKBotSetup.exe", "/S", "/unpack"])
        else:
            download_file_name = f"{DOWNLOAD_PATH}\\MKBotSetup.zip"

            os.makedirs(os.path.dirname(download_file_name), exist_ok=True)

            self.download_file(download_file_name)

            _zip = zipfile.ZipFile(download_file_name)
            _zip.extractall(DOWNLOAD_PATH)

            if self.check_sha1_hash():
                subprocess.call([f"{DOWNLOAD_PATH}\\MKBotSetup.exe", "/S", "/unpack"])

    def check_sha1_hash(self):
        if os.path.isfile(self.setupPath):
            with open(self.setupPath, "rb") as f:
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
        self.download()
        if self.check_ready_to_update():
            sys.exit(0)
        else:
            sys.exit(1)

    @staticmethod
    def can_install():
        if Updater.check_ready_to_update():
            sys.exit(0)
        else:
            sys.exit(1)


def main():
    if instance_already_running():
        sys.exit(1)

    enabled_canary = load_canary_config()
    with open("../info/version.json", "rt") as f:
        current_data = json.load(f)

    if "/s" in sys.argv:
        Updater.can_install()
    elif "/c" in sys.argv:
        ut = Updater(current_data, enabled_canary)
        ut.run()
    else:
        sys.exit(1)


if __name__ == "__main__":
    try:
        TelemetryReporter.start()
        main()
    except Exception as error:
        TelemetryReporter.Exception(error)
        traceback.print_exc()
        sys.exit(1)
