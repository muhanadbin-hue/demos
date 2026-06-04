import json
from pathlib import Path
pages = json.loads(Path('scripts/query_list.json').read_text(encoding='utf-8'))
with open('scripts/query_list_js.txt', 'w', encoding='utf-8') as f:
    f.write('const queries = ')
    json.dump(pages, f, indent=2, ensure_ascii=False)
    f.write(';\n')
print('Wrote scripts/query_list_js.txt')
