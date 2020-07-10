from packaging import version
import requests
import json
import os
import sys
import zipfile


class updater:
    def __init__(self):
        with open('../info/version.json', 'rt') as f:
            self.cur = version.parse(json.load(f)['version'])
        try:
            res = requests.get(
                'https://mgylabs.gitlab.io/discord-bot/version.json')
            res.raise_for_status()
        except:
            sys.exit(1)
        data = res.json()
        self.last = version.parse(data['last-version'])
        self.tags = data['tags']

    def check_update(self):
        return self.last > self.cur

    def isnewversion(self):
        if self.check_update():
            try:
                r = requests.get(
                    'https://gitlab.com/mgylabs/discord-bot/-/jobs/artifacts/{}/download?job=stable-release'.format(self.tags))
            except:
                sys.exit(1)

            download_file_name = os.getenv(
                'TEMP')+'\\mkbot-update\\MKBotSetup.zip'

            os.makedirs(os.path.dirname(download_file_name), exist_ok=True)

            with open(download_file_name, 'wb') as f:
                f.write(r.content)

            _zip = zipfile.ZipFile(download_file_name)
            _zip.extractall(os.getenv('TEMP')+'\\mkbot-update')
            sys.exit(0)
        else:
            sys.exit(1)


ut = updater()
if '/c' in sys.argv:
    ut.isnewversion()
