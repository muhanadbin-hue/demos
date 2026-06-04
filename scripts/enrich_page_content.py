from pathlib import Path

ROOT = Path('docs')

REPLACEMENTS = [
    (
        'Customers should understand what the business can help with within seconds of landing on the page.',
        'Customers can quickly see the core services, location, and contact details for this business.',
    ),
    (
        'Built to create trust before the first call.',
        'Find the services, location, and contact details for this business before you call.',
    ),
    (
        'A more visual first impression for customers.',
        'A clear service-focused overview for customers.',
    ),
    (
        'Professional online presence',
        'Service details at a glance',
    ),
    (
        'Clear contact pathway',
        'Direct contact and location details',
    ),
    (
        'Strong local reputation',
        'Trusted local service details',
    ),
    (
        'Local beauty salon in Macquarie Park',
        'Beauty services, booking details, and local contact information',
    ),
    (
        'Local hair salon in North Ryde',
        'Haircuts, styling, colour, and treatment information at a glance',
    ),
]

changed = []
for page_dir in sorted(ROOT.glob('*')):
    if not page_dir.is_dir():
        continue
    html_path = page_dir / 'index.html'
    if not html_path.exists():
        continue

    text = html_path.read_text(encoding='utf-8')
    original = text
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)

    if text != original:
        html_path.write_text(text, encoding='utf-8')
        changed.append(page_dir.name)

print('UPDATED_PAGES', len(changed))
for name in changed[:100]:
    print(name)
