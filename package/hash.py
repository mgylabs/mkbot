import hashlib
import json


def file_hash():
    with open('MKBotSetup.exe', 'rb') as f:
        setup = f.read()

    sha1Hash = hashlib.sha1(setup)

    with open('public/version.json', 'rt') as f:
        data = json.load(f)

    data['sha1'] = sha1Hash.hexdigest()

    with open('public/version.json', 'wt') as f:
        json.dump(data, f)


file_hash()
