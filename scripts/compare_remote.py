import urllib.request
import urllib.error
import pathlib
import difflib

base = 'https://raw.githubusercontent.com/muhanadbin-hue/demos/main/docs/'
paths = [
    'all-about-ibrows-71b3559b',
    '4-station-co-west-ryde-4d6114d4',
    'arm-automotive-mobile-mechanic-61f9ead6',
    'as-usual-771bb0a4',
    'baptistcare-hopecleaning-1eb25755',
    'breakpoint-cafe-parking-available-on-graf-ave-575fa927',
    'hair-attack-247cdd31',
    'daniele-mosman-handyman-c4d1d2f5',
    'neelgri-cafe-vegan-vegetarian-cde41462',
    'lpd-automotive-1ac5f528',
]

print('RESULTS')
for name in paths:
    local_path = pathlib.Path('docs') / name / 'index.html'
    if not local_path.exists():
        print(f'MISSING LOCAL: {name}')
        continue
    local = local_path.read_bytes()
    url = base + name + '/index.html'
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            remote = r.read()
    except urllib.error.HTTPError as e:
        print(f'REMOTE ERROR {name}: HTTP {e.code}')
        continue
    except Exception as e:
        print(f'REMOTE ERROR {name}: {e}')
        continue
    local_text = local.decode('utf-8', errors='replace').replace('\r\n', '\n').splitlines()
    remote_text = remote.decode('utf-8', errors='replace').replace('\r\n', '\n').splitlines()
    status = 'MATCH' if local_text == remote_text else 'DIFF'
    print(f'{name}: {status}')
    if status == 'DIFF':
        diff = list(difflib.unified_diff(local_text[:200], remote_text[:200], lineterm=''))
        print('\n'.join(diff[:20]))
