import json
import os
import pickle
import sys

from mgylabs.utils.config import USER_DATA_PATH
from mgylabs.utils.version import VERSION

LOCALAPPDATA = os.getenv("LOCALAPPDATA")


def is_development_mode():
    return not getattr(sys, "frozen", False) or ("--debug") in sys.argv


if is_development_mode():
    loc = "..\\..\\"
    EXT_CONFIG_PATH = "..\\data\\extensions.json"
    EXT_BIN_PATH = "..\\data\\ext.bin"
else:
    if VERSION.is_canary():
        loc = os.getenv("USERPROFILE") + "\\.mkbot-canary\\"
    else:
        loc = os.getenv("USERPROFILE") + "\\.mkbot\\"
    EXT_CONFIG_PATH = f"{USER_DATA_PATH}\\extensions.json"
    EXT_BIN_PATH = f"{USER_DATA_PATH}\\ext.bin"

extensions_path = loc + "extensions"

if os.path.isfile(loc + "extensions\\extensions.json"):
    with open(loc + "extensions\\extensions.json", "rt") as f:
        default_exts = json.load(f)["extensions"]
else:
    default_exts = {}

with open(EXT_CONFIG_PATH, "rt") as f:
    exts = json.load(f)["extensions"]


def get_enabled_extensions():
    return [
        (
            f"{x['id']}/{default_exts[x['id']]['cwd']}",
            default_exts[x["id"]].get("main", None),
        )
        for x in exts
        if x.get("enabled", False) and ("id" in x)
    ]


def find_available_extension(name: str):
    with open(loc + "extensions\\extensions.json", "rt") as f:
        _default_exts = json.load(f)["extensions"]
    return _default_exts.get(name.lower(), None)


def set_enabled(ext_id: str):
    with open(EXT_CONFIG_PATH, "rt") as f:
        exts_list = json.load(f)
    find = False
    for i in exts_list["extensions"]:
        if i["id"] == ext_id:
            find = True
            if not i["enabled"]:
                i["enabled"] = True
            break

    if not find:
        exts_list["extensions"].append({"id": ext_id, "enabled": True})

    if ext_id in default_exts:
        p = f"{extensions_path}/{ext_id}/{default_exts[ext_id]['cwd']}"
        if p not in sys.path:
            sys.path.append(p)

    with open(EXT_CONFIG_PATH, "wt") as f:
        json.dump(exts_list, f, indent=4, ensure_ascii=False)


def save_commit(name, sha):
    if not os.path.isfile(EXT_BIN_PATH):
        data = {}
    else:
        with open(EXT_BIN_PATH, "rb") as f:
            data = pickle.load(f)
    data[name] = sha
    with open(EXT_CONFIG_PATH, "wb") as f:
        pickle.dump(data, f)


def load_commit(name):
    if not os.path.isfile(EXT_CONFIG_PATH):
        return None
    else:
        with open(EXT_CONFIG_PATH, "rb") as f:
            data = pickle.load(f)
        return data.get("name", None)


def get_gitlab_oauth():
    d = {
        "client_id": "7da5dcef489bfa42b218ab346fe4d574dcd43d674757d44705732c7bba441263",
        "auth_url": "https://gitlab.com/oauth/authorize",
        "redirect_uri": "http://localhost:8080",
        "scopes": ["read_api"],
    }
    return d
