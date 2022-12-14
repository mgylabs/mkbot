import datetime
import json
import os
import sys

import requests
import yaml

base_url = "https://api.github.com"
if os.getenv("GITHUB_TOKEN") != None:
    req_headers = {"Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"}
else:
    req_headers = {}


class BuildType:
    Stable = 0
    Beta = 1
    Canary = 2


def requests_API(method, link, datadict=None):
    method = method.upper()
    if method == "POST":
        x = requests.post(base_url + link, json=datadict, headers=req_headers)
    elif method == "PUT":
        x = requests.put(base_url + link, json=datadict, headers=req_headers)
    elif method == "GET":
        x = requests.get(base_url + link, headers=req_headers)
    elif method == "PATCH":
        x = requests.patch(base_url + link, json=datadict, headers=req_headers)
    elif method == "DELETE":
        x = requests.delete(base_url + link, headers=req_headers)
    else:
        return
    return x


def isfile(filename):
    return os.path.isfile(filename)


def to_list_version(v):
    return list(map(int, (v.split("."))))


def list_to_version_str(ls):
    return ".".join(map(str, ls))


def isnewupdate(base, last):
    return base[:-1] != last[:-1]


def save_version_txt(version):
    with open("version.txt", "wt") as f:
        f.write(version)


def find_asset(assets):
    asset = None
    for d in assets:
        if d["label"].lower().startswith("mkbotsetup-"):
            asset = d
            break

    return asset


def build():
    with open("package/info/version.json", "rt") as f:
        cur = json.load(f)

    cur["version"] = cur["version"].replace("-dev", ".0")

    if isfile("output/last_version.txt"):
        with open("output/last_version.txt", "rt") as f:
            last = f.readline()
    else:
        last = cur["version"]

    cur_ver = to_list_version(cur["version"])
    try:
        last_ver = to_list_version(last)
    except Exception:
        last_ver = cur_ver

    if isnewupdate(cur_ver, last_ver):
        cur_ver[3] += 1
        final = cur_ver
    else:
        last_ver[3] += 1
        final = last_ver

    new_ver = ".".join(map(str, final))
    cur["version"] = f"{new_ver}-dev"

    os.makedirs("output", exist_ok=True)

    with open("output/last_version.txt", "wt") as f:
        f.write(new_ver)

    with open("package/info/version.json", "wt") as f:
        json.dump(cur, f)


def release():
    with open("package/info/version.json", "rt") as f:
        package_version_data = json.load(f)

    package_version_data["version"] = package_version_data["version"].replace(
        "-dev", ".0"
    )

    os.makedirs(".public", exist_ok=True)
    tag_name = os.getenv("CI_COMMIT_TAG")

    try:
        res = requests.get("https://mgylabs.gitlab.io/mulgyeol-mkbot/version.json")
        res.raise_for_status()

        last_version_data = res.json()
    except Exception:
        last_version_data = {
            "name": "MK Bot",
            "last-version": "0.0.0.0",
            "tags": None,
            "canary": {},
        }

    if "-rc" in tag_name:
        last_version_data["canary"] = {
            "last-version": package_version_data["version"],
            "tags": tag_name,
        }
    else:
        with open("output/last_version.txt", "rt") as f:
            info = f.readline()

        package_version_data["version"] = ".".join(info.split(".")[:3])

        with open("package/info/version.json", "wt") as f:
            json.dump(package_version_data, f)

        last_version_data["last-version"] = info
        last_version_data["tags"] = tag_name

    with open(".public/version.json", "wt") as f:
        json.dump(last_version_data, f)


def create_temp_changelog(build_type, version=None, commit=None):
    changelogs = []
    index_box = {}
    if build_type == BuildType.Stable:
        templog = []
    elif build_type == BuildType.Beta:
        templog = [
            f"## Try new features with Mulgyeol MK Bot Beta\n### 🧭 Feeling adventurous? Preview upcoming features before they’re released.\n> **Version** {version} Beta\n> **Commit** {commit}\n"
        ]
    else:
        templog = [
            f"## Nightly build for developers\n### Be warned: Canary can be unstable.\n> **Version** {version} Canary\n> **Commit** {commit}\n"
        ]

    for dirpath, _, filenames in os.walk("changelogs/unreleased"):
        for name in filenames:
            with open(os.path.join(dirpath, name), "rt", encoding="utf-8") as f:
                t: dict = yaml.safe_load(f)
                if t != None:
                    t = {k: v for k, v in t.items() if v != None}
                    changelogs.append(t)

    for ch in changelogs:
        if ch.get("pull_request", None) != None:
            string = f"* {ch.get('title', '')} (#{ch.get('pull_request')})"
        else:
            string = f"* {ch.get('title', '')}"
        if ch["type"] in index_box:
            index_box[ch.get("type", "others")].append(string)
        else:
            index_box[ch.get("type", "others")] = [string]

    for k, v in index_box.items():
        templog.append(f"## {k.capitalize()}")
        templog += v
        templog.append("\n")

    with open("temp_changelog.md", "wt", encoding="utf-8") as f:
        f.write("\n".join(templog))


def update_changelog(version):
    changelogs = []
    index_box = {}
    templog = [f"\n## {version} ({str(datetime.date.today())})"]

    for dirpath, _, filenames in os.walk("changelogs/unreleased"):
        for name in filenames:
            with open(os.path.join(dirpath, name), "rt", encoding="utf-8") as f:
                t: dict = yaml.safe_load(f)
                if t != None:
                    t = {k: v for k, v in t.items() if v != None}
                    changelogs.append(t)

    for ch in changelogs:
        if ch.get("pull_request", None) != None:
            string = f"* {ch.get('title', '')} (#{ch.get('pull_request')})"
        else:
            string = f"* {ch.get('title', '')}"
        if ch["type"] in index_box:
            index_box[ch.get("type", "others")].append(string)
        else:
            index_box[ch.get("type", "others")] = [string]

    for k, v in index_box.items():
        templog.append(f"### {k.capitalize()}")
        templog += v
        templog.append("\n")

    with open("CHANGELOG.md", "rt", encoding="utf-8") as f:
        old = f.readlines()

    old.insert(1, "\n".join(templog))

    with open("CHANGELOG.md", "wt", encoding="utf-8") as f:
        f.writelines(old)


def update_AssemblyInfo(version):
    with open("src/console/Properties/AssemblyInfo.cs", "rt", encoding="utf-8") as f:
        asi = f.read()
    asi = asi.replace("MK Bot - OSS", "MK Bot").replace("0.0.1.0", version)
    with open("src/console/Properties/AssemblyInfo.cs", "wt", encoding="utf-8") as f:
        f.write(asi)


def github_build():
    with open("package/info/version.json", "rt") as f:
        package_version_data = json.load(f)

    package_version_data["version"] = package_version_data["version"].replace(
        "-dev", "-beta"
    )
    package_version_data["commit"] = os.getenv("GITHUB_SHA")

    with open("package/info/version.json", "wt") as f:
        json.dump(package_version_data, f)

    save_version_txt(package_version_data["version"])
    update_AssemblyInfo(package_version_data["version"].replace("-beta", ""))


def get_last_build_version_number_commit(asset):
    if asset != None:
        _, release_type, ver, _ = asset["label"].split("-")
        build_list_version = to_list_version(".".join(ver.split(".")[:-1]))
        build_number = build_list_version[3] if len(build_list_version) > 3 else 1
        if release_type.lower() == "stable":
            build_commit = None
        else:
            build_commit = ver.split(".")[-1]
    else:
        build_number = 1
        build_commit = None
        build_list_version = [0, 0, 0, 0]

    return build_list_version, build_number, build_commit


def github_release(build_type):
    class BuildInfo:
        def __init__(self, list_version, build_number, commit) -> None:
            self.list_version = list_version
            self.number = build_number
            self.commit = commit

    with open("package/info/version.json", "rt") as f:
        package_version_data = json.load(f)

    cur_commit = os.getenv("GITHUB_SHA")
    base_version = package_version_data["version"].split("-")[0]
    list_version = to_list_version(base_version)

    res = requests_API("GET", "/repos/mgylabs/mulgyeol-mkbot/releases/tags/beta")
    asset = find_asset(res.json().get("assets"))
    beta_build = BuildInfo(*get_last_build_version_number_commit(asset))

    res = requests_API("GET", "/repos/mgylabs/mulgyeol-mkbot/releases/tags/canary")
    asset = find_asset(res.json().get("assets"))
    canary_build = BuildInfo(*get_last_build_version_number_commit(asset))

    if canary_build.list_version[:3] == beta_build.list_version[:3]:
        if canary_build.list_version[:3] == list_version[:3]:
            last_build = (
                canary_build if canary_build.number > beta_build.number else beta_build
            )
    elif canary_build.list_version[:3] == list_version[:3]:
        last_build = canary_build
    elif beta_build.list_version[:3] == list_version[:3]:
        last_build = beta_build
    else:
        last_build = None

    if last_build is None:
        list_version[3] = 1
    elif last_build.commit != cur_commit:
        list_version[3] = last_build.number + 1
    else:
        list_version[3] = last_build.number

    version_str = list_to_version_str(list_version)

    if build_type == BuildType.Stable:
        package_version_data["version"] = version_str
    elif build_type == BuildType.Beta:
        package_version_data["version"] = version_str + "-beta2"
    else:
        package_version_data["version"] = version_str + "-beta"

    package_version_data["commit"] = os.getenv("GITHUB_SHA")

    with open("package/info/version.json", "wt") as f:
        json.dump(package_version_data, f)

    if build_type == BuildType.Stable:
        save_version_txt(version_str)
    else:
        save_version_txt(f"{version_str}.{package_version_data['commit'][:7]}")

    update_AssemblyInfo(version_str)
    create_temp_changelog(build_type, version_str, package_version_data["commit"])
    update_changelog(list_to_version_str(list_version[:3]))


def github_bump_version():
    with open("package/info/version.json", "rt") as f:
        package_version_data = json.load(f)

    next_version = to_list_version(package_version_data["version"].replace("-dev", ""))

    if next_version[2] == 0:
        next_version[1] += 1
        package_version_data["version"] = f"{list_to_version_str(next_version)}-dev"

        with open("package/info/version.json", "wt") as f:
            json.dump(package_version_data, f)


def github_revert_version():
    with open("package/info/version.json", "rt") as f:
        package_version_data = json.load(f)

    next_version = to_list_version(package_version_data["version"].replace("-dev", ""))

    if next_version[2] == 0:
        next_version[1] -= 1
        package_version_data["version"] = f"{list_to_version_str(next_version)}-dev"

        with open("package/info/version.json", "wt") as f:
            json.dump(package_version_data, f)


if "-b" in sys.argv:
    build()
elif "-r" in sys.argv:
    release()
elif "-gb" in sys.argv:
    github_build()
elif "--stable" in sys.argv:
    github_release(BuildType.Stable)
elif "--beta" in sys.argv:
    github_release(BuildType.Beta)
elif "--canary" in sys.argv:
    github_release(BuildType.Canary)
elif "-gu" in sys.argv:
    github_bump_version()
elif "-gur" in sys.argv:
    github_revert_version()
