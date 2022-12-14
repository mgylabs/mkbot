import hashlib
import json
import os
import sys

import requests

base_url = "https://api.github.com"
if os.getenv("GITHUB_TOKEN") != None:
    req_headers = {"Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"}
else:
    req_headers = {}


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


def file_hash(version_str):
    with open(f"MKBotSetup-{version_str}.exe", "rb") as f:
        setup = f.read()

    sha1Hash = hashlib.sha1(setup)

    return sha1Hash.hexdigest()


def comment_on_pr():
    cur_tag = os.getenv("TAG_NAME").replace("refs/tags/", "")
    pr_list = set()
    tags = requests_API("GET", "/repos/mgylabs/mkbot/tags").json()
    if len(tags) < 2:
        return

    before_tag = None
    for i, t in enumerate(tags):
        if t["name"] == cur_tag:
            for j in range(len(tags) - (i + 1)):
                if tags[i + j + 1]["name"].startswith("v"):
                    before_tag = tags[i + j + 1]["name"]
                break
            break

    if before_tag == None:
        return

    commits_dict = requests_API(
        "GET", f"/repos/mgylabs/mkbot/compare/{before_tag}...{cur_tag}"
    ).json()["commits"]
    commits = {x["sha"] for x in commits_dict}

    for commit in commits:
        items = (
            requests_API(
                "GET",
                f"/search/issues?q=repo:mgylabs/mkbot+is:pr+is:merged+sha:{commit}",
            )
            .json()
            .get("items", None)
        )
        if items != None:
            pr_list |= {x["number"] for x in items}

    body = f"`Mulgyeol MK Bot {cur_tag}` has been released which incorporates this pull request. :tada:\n* [Release Note](https://github.com/mgylabs/mkbot/releases/tag/{cur_tag})"

    for i in pr_list:
        res = requests_API(
            "POST",
            f"/repos/mgylabs/mkbot/issues/{i}/comments",
            datadict={"body": body},
        )
        try:
            print(res.json()["html_url"])
        except Exception as e:
            print(e)
            print(res.text)


def comment_on_pr_for_pre_release(
    pre_release_tag, build_type_str: str, version_str: str
):
    cur_commit = os.getenv("GITHUB_SHA")
    pr_list = set()

    last_pre_release_commit = None
    if len(pre_release_tag["assets"]) > 0:
        asset = find_asset(pre_release_tag["assets"])
        if asset != None:
            _, _, ver, _ = asset["label"].split("-")
            last_pre_release_commit = ver.split(".")[-1]

    if last_pre_release_commit == None:
        tags = requests_API("GET", "/repos/mgylabs/mkbot/tags").json()
        if len(tags) < 2:
            return

        last_tag = None
        for i, t in enumerate(tags):
            if t["name"].startswith("v"):
                last_tag = t["name"]

        if last_tag == None:
            return

        source = last_tag
    else:
        source = last_pre_release_commit

    commits_dict = requests_API(
        "GET", f"/repos/mgylabs/mkbot/compare/{source}...{cur_commit}"
    ).json()["commits"]

    print(f"{source}...{cur_commit}")

    commits = {x["sha"] for x in commits_dict}

    for commit in commits:
        items = (
            requests_API(
                "GET",
                f"/search/issues?q=repo:mgylabs/mkbot+is:pr+is:merged+sha:{commit}",
            )
            .json()
            .get("items", None)
        )
        if items != None:
            pr_list |= {x["number"] for x in items}

    body = f"`Mulgyeol MK Bot {build_type_str.capitalize()} v{version_str}` has been released which incorporates this pull request. :tada:\n* Commit: {cur_commit}\n* [Release Note](https://github.com/mgylabs/mkbot/releases/tag/canary)"

    for i in pr_list:
        res = requests_API(
            "POST",
            f"/repos/mgylabs/mkbot/issues/{i}/comments",
            datadict={"body": body},
        )
        try:
            print(res.json()["html_url"])
        except Exception as e:
            print(e)
            print(res.text)


def upload_asset():
    with open("package/info/version.json", "rt") as f:
        version = json.load(f)["version"]
    with open("MKBotSetup.zip", "rb") as f:
        fdata = f.read()
    r = requests.post(
        os.getenv("UPLOAD_URL").replace("{?name,label}", ""),
        headers={
            "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
            "Content-Type": "application/zip",
        },
        data=fdata,
        params={
            "name": f"MKBotSetup-{version}.zip",
            "label": f"MKBotSetup-Stable-{version}-{file_hash(version)}",
        },
    )
    print(r.text)

    comment_on_pr()


def upload_pre_release_asset(tag_name: str, build_type_str: str):
    with open("package/info/version.json", "rt") as f:
        data = json.load(f)
    version = data["version"].split("-")[0]
    sha = data["commit"]

    tag = requests_API("GET", f"/repos/mgylabs/mkbot/releases/tags/{tag_name}").json()

    UPLOAD_URL = tag["upload_url"]
    REL_ID = tag["id"]

    with open("temp_changelog.md", "rt", encoding="utf-8") as f:
        chlog = f.read()
    r = requests_API(
        "PATCH", f"/repos/mgylabs/mkbot/releases/{REL_ID}", {"body": chlog}
    )
    print("Patched Changelog")

    with open("MKBotSetup.zip", "rb") as f:
        fdata = f.read()
    r = requests.post(
        UPLOAD_URL.replace("{?name,label}", ""),
        headers={
            "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
            "Content-Type": "application/zip",
        },
        data=fdata,
        params={
            "name": f"MKBot{build_type_str.capitalize()}Setup-{version}.{sha[:7]}.zip",
            "label": f"MKBotSetup-{build_type_str.capitalize()}-{version}.{sha}-{file_hash(f'{version}.{sha[:7]}')}",
        },
    )

    print("Uploaded Setup")

    if len(tag["assets"]) > 0:
        asset = find_asset(tag["assets"])
        if asset != None:
            r = requests_API(
                "DELETE", f'/repos/mgylabs/mkbot/releases/assets/{asset["id"]}'
            )
            print("Deleted", r.url)

    comment_on_pr_for_pre_release(tag, build_type_str, version)


def create_pull_request():
    TAG_NAME = os.getenv("TAG_NAME").replace("refs/tags/", "")
    BASE_REF = os.getenv("BASE_REF", "main").replace("refs/heads/", "")
    res = requests_API(
        "POST",
        "/repos/mgylabs/mkbot/pulls",
        {
            "title": f"Update CHANGELOG.md for {TAG_NAME}",
            "head": f"update-changelog-for-{TAG_NAME}",
            "base": BASE_REF,
            "body": f"## Summary of the Pull Request\n* This PR updates CHANGELOG.md for {TAG_NAME}.",
        },
    )
    print(res.text)
    if "number" in res.json():
        res = requests_API(
            "PATCH",
            f"/repos/mgylabs/mkbot/issues/{res.json()['number']}",
            {"labels": ["CHANGELOG"]},
        )
        print(res.text)

    print(
        f"::set-output name=d_url::https://github.com/mgylabs/mkbot/releases/tag/{TAG_NAME}"
    )


def check_last_commit():
    cur_commit = os.getenv("GITHUB_SHA")
    res = requests_API("GET", "/repos/mgylabs/mkbot/releases/tags/canary")

    asset = find_asset(res.json()["assets"])
    last_build_commit = None
    if asset != None:
        _, _, version, _ = asset["label"].split("-")
        last_build_commit = version.split(".")[-1]
    is_new = last_build_commit != cur_commit
    if is_new:
        print("::set-output name=is_new::true")
    else:
        print("::set-output name=is_new::false")


def create_new_branch():
    TAG_NAME = os.getenv("TAG_NAME")
    SHA = requests_API("GET", "/repos/mgylabs/mkbot/git/ref/heads/main").json()[
        "object"
    ]["sha"]
    print(SHA)
    res = requests_API(
        "POST",
        "/repos/mgylabs/mkbot/git/refs",
        {"ref": f"refs/heads/update-changelog-for-{TAG_NAME[10:]}", "sha": SHA},
    )
    print(res.text)
    with open("head_sha.txt", "wt") as f:
        f.write(SHA)


def find_asset(assets):
    asset = None
    for d in assets:
        if d["label"].lower().startswith("mkbotsetup-"):
            asset = d
            break

    return asset


if "-ua" in sys.argv:
    upload_asset()
elif "-uca" in sys.argv:
    upload_pre_release_asset("canary", "canary")
elif "-ubeta" in sys.argv:
    upload_pre_release_asset("beta", "beta")
elif "-cp" in sys.argv:
    create_pull_request()
elif "-check" in sys.argv:
    check_last_commit()
elif "--create-new-branch" in sys.argv:
    create_new_branch()
