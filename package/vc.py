import json
import sys, os

def isfile(filename):
    return os.path.isfile(filename)

def version(v):
    return list(map(int, (v.split("."))))

def isnewupdate(base, last):
    return base[:-1] != last[:-1]

def build():
    with open('package/data/version.json', 'rt') as f:
        cur = json.load(f)

    if isfile('output/last_version.txt'):
        with open('output/last_version.txt', 'rt') as f:
            last = f.readline()
    else:
        last = cur['version']

    cur_ver = version(cur['version'])
    last_ver = version(last)

    if isnewupdate(cur_ver, last_ver):
        cur_ver[3] += 1
        final = cur_ver
    else:
        last_ver[3] += 1
        final = last_ver

    last = '.'.join(map(str, final))

    os.makedirs('output', exist_ok=True)

    with open('output/last_version.txt', 'wt') as f:
        f.write(last)

def release():
    with open('output/last_version.txt', 'rt') as f:
        info = f.readline()

    with open('public/version.json', 'rt') as f:
        public = json.load(f)
    
    public['last-version'] = info

    with open('public/version.json', 'wt') as f:
        json.dump(public, f) 

if '-b' in sys.argv:
    build()
elif '-r' in sys.argv:
    release()

build()