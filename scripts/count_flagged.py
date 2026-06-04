import json
from pathlib import Path

p = Path('scripts/audit_report.json')
obj = json.loads(p.read_text(encoding='utf-8'))
flagged = [x for x in obj if x.get('needs_review')]
print('total_pages', len(obj))
print('flagged_pages', len(flagged))
print('sample_flagged', [x['directory'] for x in flagged[:10]])
