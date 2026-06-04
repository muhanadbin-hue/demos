import json, html
from pathlib import Path
pages = json.loads(Path('scripts/page_metadata.json').read_text(encoding='utf-8'))
queries = []
for p in pages:
    title = html.unescape(p['title'])
    business = title.split('|')[0].strip()
    business = business.split('-')[0].strip()
    business = business.split(':')[0].strip()
    business = business.replace('  ', ' ')
    queries.append({
        'directory': p['directory'],
        'query': business,
        'expected_addresses': p['addresses'],
        'phones': p['phones'],
        'title': title,
    })
Path('scripts/query_list.json').write_text(json.dumps(queries, indent=2, ensure_ascii=False), encoding='utf-8')
print('Wrote scripts/query_list.json')
