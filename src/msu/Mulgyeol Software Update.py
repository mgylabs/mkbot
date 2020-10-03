from packaging import version
import requests
import json
import os
import sys
import zipfile
import hashlib
import traceback


class updater:
    def __init__(self):
        with open('../info/version.json', 'rt') as f:
            self.cur = version.parse(json.load(f)['version'])
        try:
            res = requests.get(
                'https://mgylabs.gitlab.io/mulgyeol-mkbot/version.json')
            res.raise_for_status()
        except:
            sys.exit(1)
        data = res.json()
        self.last = version.parse(data['last-version'])
        self.tags = data['tags']
        self.sha1Hash = data['sha1']
        self.setupPath = os.getenv('TEMP') + '\\mkbot-update\\MKBotSetup.exe'

    def check_update(self):
        return self.last > self.cur

    def download(self):
        try:
            r = requests.get(
                'https://gitlab.com/mgylabs/mulgyeol-mkbot/-/jobs/artifacts/{}/download?job=stable-release'.format(self.tags))
            r.raise_for_status()
        except:
            sys.exit(1)

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
            return hashlib.sha1(file_data).hexdigest() == self.sha1Hash
        else:
            return False

    def isnewversion(self):
        if self.check_update():
            if self.check_sha1_hash():
                sys.exit(0)
            self.download()
            if self.check_sha1_hash():
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            sys.exit(1)


try:
    ut = updater()
    if '/c' in sys.argv:
        ut.isnewversion()
except Exception as e:
    traceback.print_exc()
    sys.exit(1)
