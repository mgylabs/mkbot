import hashlib
import json
import os
import sys
import threading
import traceback

config_sema = threading.BoundedSemaphore()

LOCALAPPDATA = os.getenv("LOCALAPPDATA")


def is_development_mode():
    return not getattr(sys, "frozen", False) or ("--debug") in sys.argv


if is_development_mode():
    CONFIG_PATH = "../data/config.json"
    MGCERT_PATH = "../data/mgcert.json"
    USER_DATA_PATH = "../data"
else:
    CONFIG_PATH = f"{LOCALAPPDATA}\\Mulgyeol\\Mulgyeol MK Bot\\data\\config.json"
    MGCERT_PATH = f"{LOCALAPPDATA}\\Mulgyeol\\Mulgyeol MK Bot\\data\\mgcert.json"
    USER_DATA_PATH = f"{LOCALAPPDATA}\\Mulgyeol\\Mulgyeol MK Bot\\data"


class SettingItem:
    def __init__(self, value=None) -> None:
        self.value = value

    def __get__(self, instance, cls):
        return self.value

    def __set__(self, instance, value):
        self.value = value


class Settings:
    discordToken = SettingItem("Your Token")
    kakaoToken = SettingItem("Your Token")
    commandPrefix = SettingItem(".")
    messageColor = SettingItem("#FAA61A")
    disabledPrivateChannel = SettingItem(False)
    connectOnStart = SettingItem(False)
    gitlabToken = SettingItem("")
    mgylabsToken = SettingItem("")
    canaryUpdate = SettingItem(False)

    def __init__(self, data):
        self.update_dict(data)

    @property
    def __data__(self) -> dict:
        return {
            k: v for k, v in Settings.__dict__.items() if isinstance(v, SettingItem)
        }

    @property
    def __key__(self):
        return [k for k, v in Settings.__dict__.items() if isinstance(v, SettingItem)]

    @property
    def __default_attr_key__(self):
        return [
            k for k, v in Settings.__dict__.items() if not isinstance(v, SettingItem)
        ]

    def load(self):
        with open(CONFIG_PATH, "rt", encoding="utf-8") as f:
            js: dict = json.load(f)
        self.update_dict(js)

    def update_dict(self, data: dict):
        for k, v in data.items():
            setattr(Settings, k, SettingItem(v))

    def save(self):
        with open(CONFIG_PATH, "wt", encoding="utf-8") as f:
            json.dump(
                {k: v.value for k, v in self.__data__.items()},
                f,
                indent=4,
                ensure_ascii=False,
            )

    def get(self, key, default=None):
        if self.__contains__(key):
            return self.__getitem__(key)
        else:
            return default

    def __getitem__(self, key):
        return self.__getattribute__(key)

    def __contains__(self, key: str):
        return key in self.__key__

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __delitem__(self, key):
        self.__delattr__(key)

    def __setattr__(self, key: str, value: str) -> None:
        if key in self.__default_attr_key__:
            raise KeyError(f"This key is not available: {key}")

        with config_sema:
            self.load()
            setattr(Settings, key, SettingItem(value))
            self.save()

    def __delattr__(self, key):
        if key in self.__default_attr_key__:
            raise KeyError(f"This key is not available: {key}")

        with config_sema:
            self.load()
            delattr(Settings, key)
            self.save()


class Version:
    def __init__(self, version_str, commit):
        version_str = version_str.split("-")
        self.commit = commit
        self.base_version = version_str[0]
        self.tuple_version = tuple(self.base_version.split("."))
        self.canary = (
            True
            if (
                len(version_str) > 1
                and version_str[1] == "beta"
                and self.commit != None
            )
            else False
        )
        self.tag = f"v{self.base_version}"

    def is_release_build(self):
        return (not is_development_mode()) and (self.commit is not None)

    def is_canary(self) -> bool:
        return self.canary

    def __str__(self) -> str:
        if is_development_mode():
            return "Dev"
        if self.commit == None:
            return f"{self.base_version} Test Mode"
        if self.is_canary():
            return f"{self.base_version} Canary"
        else:
            return f"{self.base_version} Stable"


def invoke():
    if os.path.isfile(CONFIG_PATH):
        with open(CONFIG_PATH, "rt", encoding="utf-8") as f:
            TOKEN = json.load(f)
    else:
        return {}

    sch_url = "https://mgylabs.gitlab.io/mulgyeol-mkbot/config.schema"

    if TOKEN.get("$schema", None) != sch_url:
        with open(CONFIG_PATH, "wt", encoding="utf-8") as f:
            if "$schema" in TOKEN:
                TOKEN["$schema"] = sch_url
                json.dump(TOKEN, f, indent=4, ensure_ascii=False)
            else:
                json.dump(
                    {"$schema": sch_url, **TOKEN}, f, indent=4, ensure_ascii=False
                )

    return TOKEN


def add_data(key, value):
    with open(CONFIG_PATH, "rt", encoding="utf-8") as f:
        TOKEN = json.load(f)

    TOKEN[key] = value

    with open(CONFIG_PATH, "wt", encoding="utf-8") as f:
        json.dump(TOKEN, f, indent=4, ensure_ascii=False)


def get_mkbot_version():
    try:
        with open("../info/version.json", "rt", encoding="utf-8") as f:
            d = json.load(f)
        return Version(d["version"], d["commit"])
    except Exception:
        traceback.print_exc()
        return None


def get_discriminator(key):
    return hashlib.sha1(key.encode()).hexdigest()


CONFIG = Settings(invoke())
VERSION = get_mkbot_version()
DISCRIMINATOR = get_discriminator(CONFIG.discordToken)
