import hashlib
import json
import os


def file_hash():
    with open("MKBotSetup.exe", "rb") as f:
        setup = f.read()

    sha1Hash = hashlib.sha1(setup)

    with open("public/version.json", "rt") as f:
        data = json.load(f)

    tag_name = os.getenv("CI_COMMIT_TAG")

    if "-rc" in tag_name:
        data["canary"]["sha1"] = sha1Hash.hexdigest()
    else:
        data["sha1"] = sha1Hash.hexdigest()

    with open("public/version.json", "wt") as f:
        json.dump(data, f)


file_hash()
