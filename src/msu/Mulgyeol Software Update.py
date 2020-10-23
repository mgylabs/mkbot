from packaging import version
import requests
import json
import os
import sys
import zipfile
import hashlib
import traceback
import msvcrt  # pylint: disable=import-error


def load_canary_config():
    try:
        with open('../data/config.json', 'rt', encoding='utf-8') as f:
            TOKEN = json.load(f)
        return TOKEN['canaryUpdate']
    except:
        return False


def instance_already_running():
    fd = os.open(f"{os.getenv('TEMP')}\\mkbot_msu.lock",
                 os.O_WRONLY | os.O_CREAT)

    try:
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        already_running = False
    except IOError:
        already_running = True

    return already_running


class VersionInfo:
    def __init__(self, version, tags, sha):
        self.version = version
        self.tags = tags
        self.sha = sha


class Updater:
    def __init__(self, enabled_canary=False):
        with open('../info/version.json', 'rt') as f:
            self.current_version = version.parse(json.load(f)['version'])

        if self.current_version.release[3] == 0:
            sys.exit(1)

        res = requests.get(
            'https://mgylabs.gitlab.io/mulgyeol-mkbot/version.json')
        res.raise_for_status()
        data = res.json()

        self.setupPath = os.getenv('TEMP') + '\\mkbot-update\\MKBotSetup.exe'
        self.enabled_canary = enabled_canary

        self.last_stable = VersionInfo(version.parse(
            data['last-version']), data['tags'], data['sha1'])

        canary_data: dict = data.get('canary', {})
        if (canary_data.get('last-version') and canary_data.get('tags') and canary_data.get('sha1')):
            self.last_canary = VersionInfo(version.parse(
                canary_data['last-version']), canary_data['tags'], canary_data['sha1'])
        else:
            self.last_canary = None

        if self.last_stable.version > self.current_version:
            self.target = self.last_stable
        elif self.enabled_canary and self.last_canary and self.last_canary.version > self.current_version:
            self.target = self.last_canary
        else:
            sys.exit(1)

    def download(self):
        r = requests.get(
            'https://gitlab.com/mgylabs/mulgyeol-mkbot/-/jobs/artifacts/{}/download?job=stable-release'.format(self.target.tags))
        r.raise_for_status()

        download_file_name = os.getenv(
            'TEMP') + '\\mkbot-update\\MKBotSetup.zip'

        os.makedirs(os.path.dirname(download_file_name), exist_ok=True)

        with open(download_file_name, 'wb') as f:
            f.write(r.content)

        _zip = zipfile.ZipFile(download_file_name)
        _zip.extractall(os.getenv('TEMP') + '\\mkbot-update')

    def check_sha1_hash(self):
        if os.path.isfile(self.setupPath):
            with open(self.setupPath, 'rb') as f:
                file_data = f.read()
            return hashlib.sha1(file_data).hexdigest() == self.target.sha
        else:
            return False

    def run(self):
        if self.check_sha1_hash():
            sys.exit(0)
        self.download()
        if self.check_sha1_hash():
            sys.exit(0)
        else:
            sys.exit(1)

    def can_install(self):
        if self.check_sha1_hash():
            sys.exit(0)
        else:
            sys.exit(1)


def main():
    if instance_already_running():
        sys.exit(1)

    enabled_canary = load_canary_config()

    if '/s' in sys.argv:
        ut = Updater(enabled_canary)
        ut.can_install()
    elif '/c' in sys.argv:
        ut = Updater(enabled_canary)
        ut.run()


try:
    main()
except Exception as e:
    traceback.print_exc()
    sys.exit(1)
