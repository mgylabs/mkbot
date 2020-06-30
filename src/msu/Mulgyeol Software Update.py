from packaging import version
import requests
import json
import os
import sys
import zipfile
import win32api


class updater:
    def __init__(self):
        with open('../info/version.json', 'rt') as f:
            self.cur = version.parse(json.load(f)['version'])

        res = requests.get(
            'https://mgylabs.gitlab.io/discord-bot/version.json')
        data = res.json()
        self.last = version.parse(data['last-version'])
        self.tags = data['tags']

    def check_update(self):
        return self.last > self.cur

    def isnewversion(self):
        if self.check_update():
            r = requests.get(
                'https://gitlab.com/mgylabs/discord-bot/-/jobs/artifacts/{}/download?job=stable-release'.format(self.tags))

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

    def run(self, autorun=False):
        if self.check_update():
            if autorun:
                param = '/S /autorun'
            else:
                param = '/S'
            win32api.ShellExecute(None, "open", os.getenv(
                'TEMP')+'\\mkbot-update\\MKBotSetup.exe', param, None, 0)
        else:
            sys.exit(1)


ut = updater()
if '/c' in sys.argv:
    ut.isnewversion()
elif '/autorun' in sys.argv:
    ut.run(True)
else:
    ut.run(False)
