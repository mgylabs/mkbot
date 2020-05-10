from packaging import version
import requests
import json

class updater:
    def __init__(self):
        with open('../data/version.json', 'rt') as f:
            self.cur = version.parse(json.load(f)['version'])

        res = requests.get('https://mgylabs.gitlab.io/discord-bot/version.json')
        self.last = version.parse(res.json()['last-version'])

    def check_update(self):
        return self.last > self.cur

    def run(self):
        if self.check_update():
            r = requests.get('https://gitlab.com/mgylabs/discord-bot/-/jobs/artifacts/master/download?job=production')
        with open('setup.zip', 'wb') as f:
            f.write(r.content)

