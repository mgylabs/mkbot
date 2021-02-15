import datetime
import json
import os
import sys

import requests
import yaml


def isfile(filename):
    return os.path.isfile(filename)


def version(v):
    return list(map(int, (v.split("."))))


def list_to_version_str(ls):
    return ".".join(map(str, ls))


def isnewupdate(base, last):
    return base[:-1] != last[:-1]


def save_version_txt(version):
    with open("version.txt", "wt") as f:
        f.write(version)


def build():
    with open("package/info/version.json", "rt") as f:
        cur = json.load(f)

    cur["version"] = cur["version"].replace("-dev", ".0")

    if isfile("output/last_version.txt"):
        with open("output/last_version.txt", "rt") as f:
            last = f.readline()
    else:
        last = cur["version"]

    cur_ver = version(cur["version"])
    try:
        last_ver = version(last)
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


def create_temp_changelog(stable, commit=None):
    changelogs = []
    index_box = {}
    if stable:
        templog = []
    else:
        templog = [
            f"## Nightly build for developers\n### Be warned: Canary can be unstable.\n* commit: {commit}\n"
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

    package_version_data["commit"] = os.getenv("GITHUB_SHA")

    with open("package/info/version.json", "wt") as f:
        json.dump(package_version_data, f)

    save_version_txt(package_version_data["version"])
    update_AssemblyInfo(package_version_data["version"].replace("-dev", ""))


def github_release(stable):
    with open("package/info/version.json", "rt") as f:
        package_version_data = json.load(f)

    if stable:
        package_version_data["version"] = package_version_data["version"].replace(
            "-dev", ""
        )

    package_version_data["commit"] = os.getenv("GITHUB_SHA")

    with open("package/info/version.json", "wt") as f:
        json.dump(package_version_data, f)
    if stable:
        save_version_txt(package_version_data["version"])
    else:
        save_version_txt(
            package_version_data["version"].replace(
                "-dev", f".{package_version_data['commit'][:7]} Canary"
            )
        )
    update_AssemblyInfo(package_version_data["version"].replace("-dev", ""))
    create_temp_changelog(stable, package_version_data["commit"])
    update_changelog(package_version_data["version"])


def github_bump_version():
    with open("package/info/version.json", "rt") as f:
        package_version_data = json.load(f)

    next_version = version(package_version_data["version"].replace("-dev", ""))

    if next_version[2] == 0:
        next_version[1] += 1
        package_version_data["version"] = f"{list_to_version_str(next_version)}-dev"

        with open("package/info/version.json", "wt") as f:
            json.dump(package_version_data, f)


def github_revert_version():
    with open("package/info/version.json", "rt") as f:
        package_version_data = json.load(f)

    next_version = version(package_version_data["version"].replace("-dev", ""))

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
elif "-gr" in sys.argv:
    github_release(True)
elif "-gn" in sys.argv:
    github_release(False)
elif "-gu" in sys.argv:
    github_bump_version()
elif "-gur" in sys.argv:
    github_revert_version()
