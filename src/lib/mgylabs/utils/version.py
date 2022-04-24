import json
import sys


def is_development_mode():
    return not getattr(sys, "frozen", False) or ("--debug") in sys.argv


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
        self.tag = f"v{'.'.join(self.tuple_version[:-1])}"

    def is_release_build(self):
        return (not is_development_mode()) and (self.commit is not None)

    def is_canary(self) -> bool:
        return self.canary

    @property
    def product_name(self):
        if is_development_mode() or self.commit == None:
            return "Mulgyeol MK Bot OSS"

        if self.is_canary():
            return "Mulgyeol MK Bot Canary"
        else:
            return "Mulgyeol MK Bot Stable"

    def __str__(self) -> str:
        if is_development_mode():
            return "Dev"
        if self.commit == None:
            return f"{self.base_version} Test Mode"
        if self.is_canary():
            return f"{self.base_version} Canary"
        else:
            return f"{self.base_version} Stable"


def get_mkbot_version():
    try:
        with open("../info/version.json", "rt", encoding="utf-8") as f:
            d = json.load(f)
        return Version(d["version"], d["commit"])
    except Exception:
        return None


VERSION = get_mkbot_version()
