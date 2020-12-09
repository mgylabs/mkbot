import requests
import os
import sys
import hashlib


def file_hash():
    with open('MKBotSetup.exe', 'rb') as f:
        setup = f.read()

    sha1Hash = hashlib.sha1(setup)

    return sha1Hash.hexdigest()


def upload_asset():
    version = os.getenv('TAG_NAME').replace('v', '')
    with open('MKBotSetup.zip', 'rb') as f:
        fdata = f.read()
    requests.post(os.getenv('UPLOAD_URL') + f'?name=MKBotSetup-{version}.zip&label=mkbotsetup-stable-{version}-{file_hash()}', headers={
                  'Authorization': f"Bearer {os.getenv('GITHUB_TOKEN')}", 'Content-Type': 'application/zip'}, data=fdata)


if '-ua' in sys.argv:
    upload_asset()
