import json
import sys
import os


def get_enabled_extensions():
    if getattr(sys, 'frozen', False):
        loc = os.getenv('USERPROFILE')+'\\.mkbot\\'
    else:
        loc = ''

    with open(loc+'extensions\\extensions.json', 'rt') as f:
        default_exts = json.load(f)['extensions']
    with open('..\\data\\extensions.json', 'rt') as f:
        exts = json.load(f)['extensions']
    return ['extensions.{}.{}'.format(x['id'], default_exts[x['id']]['main']) for x in exts if x.get('enabled', False) and ('id' in x)]
