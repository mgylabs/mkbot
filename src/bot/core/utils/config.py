import json
import os
import sys

LOCALAPPDATA = os.getenv('LOCALAPPDATA')

def is_development_mode():
    return (not getattr(sys, 'frozen', False) or ('--debug') in sys.argv)


if is_development_mode():
    CONFIG_PATH = '../data/config.json'
    MGCERT_PATH = '../data/mgcert.json'
    USER_DATA_PATH = '../data'
else:
    CONFIG_PATH = f"{LOCALAPPDATA}\\Mulgyeol\\Mulgyeol MK Bot\\data\\config.json"
    MGCERT_PATH = f"{LOCALAPPDATA}\\Mulgyeol\\Mulgyeol MK Bot\\data\\mgcert.json"
    USER_DATA_PATH = f"{LOCALAPPDATA}\\Mulgyeol\\Mulgyeol MK Bot\\data"

class Settings:
    def __init__(self, data):
        self.discordToken = "Your Token"
        self.kakaoToken = "Your Token"
        self.commandPrefix = "."
        self.messageColor = "#FAA61A"
        self.disabledPrivateChannel = False
        self.connectOnStart = False
        self.gitlabToken = ''
        self.canaryUpdate = False
        self.__dict__.update(data)


class Version:
    def __init__(self, version_str, commit):
        version_str = version_str.split('-')
        self.commit = commit
        self.base_version = version_str[0]
        self.tuple_version = tuple(self.base_version.split('.'))
        self.canary = True if (
            len(version_str) > 1 and version_str[1] == 'dev' and self.commit != None) else False
        self.tag = f'v{self.base_version}'

    def is_canary(self) -> bool:
        return self.canary

    def __str__(self) -> str:
        if is_development_mode():
            return f"Dev"
        if self.commit == None:
            return f"{self.base_version} Test Mode"
        if self.is_canary():
            return f"{self.base_version} Canary"
        else:
            return f"{self.base_version} Stable"


def invoke():
    with open(CONFIG_PATH, 'rt', encoding='utf-8') as f:
        TOKEN = json.load(f)

    sch_url = 'https://mgylabs.gitlab.io/mulgyeol-mkbot/config.schema'

    if TOKEN.get('$schema', None) != sch_url:
        with open(CONFIG_PATH, 'wt', encoding='utf-8') as f:
            if '$schema' in TOKEN:
                TOKEN['$schema'] = sch_url
                json.dump(TOKEN,
                          f, indent=4, ensure_ascii=False)
            else:
                json.dump({'$schema': sch_url, **TOKEN},
                          f, indent=4, ensure_ascii=False)

    return TOKEN


def add_data(key, value):
    with open(CONFIG_PATH, 'rt', encoding='utf-8') as f:
        TOKEN = json.load(f)

    TOKEN[key] = value

    with open(CONFIG_PATH, 'wt', encoding='utf-8') as f:
        json.dump(TOKEN, f, indent=4, ensure_ascii=False)


def get_mkbot_version():
    try:
        with open('../info/version.json', 'rt') as f:
            d = json.load(f)
        return Version(d['version'], d['commit'])
    except:
        return None


CONFIG = Settings(invoke())
VERSION = get_mkbot_version()
