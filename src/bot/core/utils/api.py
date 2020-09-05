import json
import sys
import os
import pickle

if getattr(sys, 'frozen', False):
    loc = os.getenv('USERPROFILE') + '\\.mkbot\\'
else:
    loc = '..\\..\\'

extensions_path = loc + 'extensions'

with open(loc + 'extensions\\extensions.json', 'rt') as f:
    default_exts = json.load(f)['extensions']
with open('..\\data\\extensions.json', 'rt') as f:
    exts = json.load(f)['extensions']


def get_enabled_extensions():
    return [(f"{x['id']}/{default_exts[x['id']]['cwd']}", '{}'.format(default_exts[x['id']]['main'])) for x in exts if x.get('enabled', False) and ('id' in x)]


def find_available_extension(name: str):
    with open(loc + 'extensions\\extensions.json', 'rt') as f:
        _default_exts = json.load(f)['extensions']
    return _default_exts.get(name.lower(), None)


def set_enabled(ext_id: str):
    with open('..\\data\\extensions.json', 'rt') as f:
        exts_list = json.load(f)
    find = False
    for i in exts_list['extensions']:
        if i['id'] == ext_id:
            find = True
            i['enabled'] = True
            break

    if not find:
        exts_list['extensions'].append({'id': ext_id, 'enabled': True})

    with open('..\\data\\extensions.json', 'wt') as f:
        json.dump(exts_list, f, indent=4, ensure_ascii=False)


def save_commit(name, sha):
    if not os.path.isfile('..\\data\\ext.bin'):
        data = {}
    else:
        with open('..\\data\\ext.bin', 'rb') as f:
            data = pickle.load(f)
    data[name] = sha
    with open('..\\data\\ext.bin', 'wb') as f:
        pickle.dump(data, f)


def load_commit(name):
    if not os.path.isfile('..\\data\\ext.bin'):
        return None
    else:
        with open('..\\data\\ext.bin', 'rb') as f:
            data = pickle.load(f)
        return data.get('name', None)


def get_gitlab_oauth():
    d = {'client_id': '7da5dcef489bfa42b218ab346fe4d574dcd43d674757d44705732c7bba441263',
         'auth_url': 'https://gitlab.com/oauth/authorize', 'redirect_uri': 'http://localhost:8080', 'scopes': ['read_api']}
    return d
