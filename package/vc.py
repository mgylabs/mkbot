import json
import sys
import os
import requests


def isfile(filename):
    return os.path.isfile(filename)


def version(v):
    return list(map(int, (v.split("."))))


def isnewupdate(base, last):
    return base[:-1] != last[:-1]


def build():
    with open('package/info/version.json', 'rt') as f:
        cur = json.load(f)

    if isfile('output/last_version.txt'):
        with open('output/last_version.txt', 'rt') as f:
            last = f.readline()
    else:
        last = cur['version']

    cur_ver = version(cur['version'])
    try:
        last_ver = version(last)
    except:
        last_ver = cur_ver

    if isnewupdate(cur_ver, last_ver):
        cur_ver[3] += 1
        final = cur_ver
    else:
        last_ver[3] += 1
        final = last_ver

    new_ver = '.'.join(map(str, final))
    cur['version'] = f'{new_ver}-dev'

    os.makedirs('output', exist_ok=True)

    with open('output/last_version.txt', 'wt') as f:
        f.write(new_ver)

    with open('package/info/version.json', 'wt') as f:
        json.dump(cur, f)


def release():
    with open('package/info/version.json', 'rt') as f:
        package_version_data = json.load(f)

    os.makedirs('.public', exist_ok=True)
    tag_name = os.getenv('CI_COMMIT_TAG')

    try:
        res = requests.get(
            'https://mgylabs.gitlab.io/mulgyeol-mkbot/version.json')
        res.raise_for_status()

        last_version_data = res.json()
    except:
        last_version_data = {'name': 'MK Bot', 'last-version': '0.0.0.0',
                             'tags': None, 'canary': {}}

    if '-rc' in tag_name:
        last_version_data['canary'] = {
            'last-version': package_version_data['version'], 'tags': tag_name}
    else:
        with open('output/last_version.txt', 'rt') as f:
            info = f.readline()

        package_version_data['version'] = info

        with open('package/info/version.json', 'wt') as f:
            json.dump(package_version_data, f)

        last_version_data['last-version'] = info
        last_version_data['tags'] = tag_name

    with open('.public/version.json', 'wt') as f:
        json.dump(last_version_data, f)


if '-b' in sys.argv:
    build()
elif '-r' in sys.argv:
    release()
