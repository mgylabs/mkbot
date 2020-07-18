import json
import sys
import os


def get_enabled_extensions():
    if getattr(sys, 'frozen', False):
        loc = os.getenv('USERPROFILE')+'\\.mkbot\\'
    else:
        loc = ''

    with open(loc+'extensions\\extensions.json', 'rt') as f:
        exts = json.load(f)['extensions']
    return ['extensions.{}.{}'.format(x['id'], x['main']) for x in exts if x.get('enabled', False) and ('id' in x) and ('main' in x)]
