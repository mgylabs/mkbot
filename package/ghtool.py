import requests
import os
import sys
import hashlib

base_url = 'https://api.github.com'
req_headers = {'Authorization': f"Bearer {os.getenv('GITHUB_TOKEN')}"}


def requests_API(method, link, datadict=None):
    method = method.upper()
    if method == "POST":
        x = requests.post(base_url + link,
                          json=datadict, headers=req_headers)
    elif method == "PUT":
        x = requests.put(base_url + link,
                         json=datadict, headers=req_headers)
    elif method == 'GET':
        x = requests.get(base_url + link, headers=req_headers)
    return x


def file_hash():
    with open('MKBotSetup.exe', 'rb') as f:
        setup = f.read()

    sha1Hash = hashlib.sha1(setup)

    return sha1Hash.hexdigest()


def comment_on_pr():
    cur_tag = os.getenv('TAG_NAME').replace('refs/tags/', '')
    pr_list = set()
    tags = requests_API('GET', '/repos/mgylabs/mulgyeol-mkbot/tags').json()
    if len(tags) < 2:
        return

    before_tag = None
    for i, t in enumerate(tags):
        if t['name'] == cur_tag:
            before_tag = tags[i + 1]['name']

    if before_tag == None:
        return

    commits_dict = requests_API(
        'GET', f'/repos/mgylabs/mulgyeol-mkbot/compare/{before_tag}...{cur_tag}').json()['commits']
    commits = {x['sha'] for x in commits_dict}

    for commit in commits:
        items = requests_API(
            'GET', f'/search/issues?q=repo:mgylabs/mulgyeol-mkbot+is:pr+is:merged+sha:{commit}').json().get('items', None)
        if items != None:
            pr_list |= {x['number'] for x in items}

    for i in pr_list:
        res = requests_API(
            'POST', f'/repos/mgylabs/mulgyeol-mkbot/issues/{i}/comments', datadict={'body': f'`Mulgyeol MK Bot {cur_tag}` has been released which incorporates this pull request. :tada:\n* [Release Note](https://github.com/mgylabs/mulgyeol-mkbot/releases/tag/{cur_tag})'})
        print(res.text)

def upload_asset():
    version = os.getenv('TAG_NAME').replace('refs/tags/', '').replace('v', '')
    with open('MKBotSetup.zip', 'rb') as f:
        fdata = f.read()
    r = requests.post(os.getenv('UPLOAD_URL').replace('{?name,label}', ''), headers={
        'Authorization': f"Bearer {os.getenv('GITHUB_TOKEN')}", 'Content-Type': 'application/zip'}, data=fdata, params={'name': f'mkbotsetup-stable-{version}-{file_hash()}', 'label': f'MKBotSetup-{version}.zip'})
    print(r.text)

    comment_on_pr()


def create_pull_request():
    TAG_NAME = os.getenv('TAG_NAME').replace('refs/tags/', '')
    res = requests_API('POST', '/repos/mgylabs/mulgyeol-mkbot/pulls',
                 {'title': f'Update CHANGELOG.md for {TAG_NAME}', 'head': f'update-changelog-for-{TAG_NAME}', 'base': 'master', 'body': f'## Summary of the Pull Request\n* This PR updates CHANGELOG.md for {TAG_NAME}.'})
    print(res.text)

if '-ua' in sys.argv:
    upload_asset()
elif '-cp' in sys.argv:
    create_pull_request()
