import json
import re
from html.parser import HTMLParser
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent / 'docs'
OUTPUT_JSON = SCRIPT_DIR / 'audit_report.json'
OUTPUT_MD = SCRIPT_DIR / 'audit_report.md'
FLAGGED = SCRIPT_DIR / 'flagged_pages.txt'

CATEGORY_TERMS = [
    'barber', 'barbershop', 'barber shop',
    'nail salon', 'nails', 'beauty bar', 'beauty salon',
    'hair salon', 'beauty', 'spa',
]
GENERIC_HINTS = [
    'clear online presence',
    'professional online presence',
    'website preview',
    'independent concept',
    'polished online presence',
    'presented with clear contact details',
    'helps customers understand',
    'helps the business easier to understand',
]

PHONE_RE = re.compile(r'0[23-78][\d\s\-\(\)]{6,}')
ADDRESS_KEYWORDS = ['nsw', 'australia', 'road', 'rd', 'street', 'st', 'avenue', 'ave', 'lane', 'ln', 'drive', 'dr', 'boulevard', 'blvd', 'court', 'ct', 'place', 'pl', 'parade', 'pde', 'square', 'sq', 'crescent', 'cres']


def normalize_phone(value):
    return re.sub(r'\D', '', value or '')


def normalize_text(value):
    if value is None:
        return ''
    value = value.lower().strip()
    value = re.sub(r'\s+', ' ', value)
    return value


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tag_stack = []
        self.title = ''
        self.headings = []
        self.text_parts = []
        self.tel_hrefs = []

    def handle_starttag(self, tag, attrs):
        self.tag_stack.append(tag)
        if tag == 'a':
            for name, value in attrs:
                if name == 'href' and value and value.startswith('tel:'):
                    self.tel_hrefs.append(value[len('tel:'):])

    def handle_endtag(self, tag):
        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()

    def handle_data(self, data):
        if not data or not data.strip():
            return
        current_tag = self.tag_stack[-1] if self.tag_stack else ''
        clean = data.strip()
        self.text_parts.append(clean)
        if current_tag == 'title':
            self.title += clean + ' '
        elif current_tag in ('h1', 'h2', 'h3'):
            self.headings.append((current_tag, clean))

    def get_text(self):
        return ' | '.join(self.text_parts)


def extract_page_data(page_dir):
    index_path = page_dir / 'index.html'
    meta_path = page_dir / '_site_meta.json'
    if not index_path.exists():
        return None
    page_html = index_path.read_text(encoding='utf-8', errors='replace')
    parser = PageParser()
    parser.feed(page_html)
    text = parser.get_text()
    normalized_text = normalize_text(text)
    phones = {normalize_phone(p) for p in PHONE_RE.findall(text)}
    phones.update({normalize_phone(p) for p in parser.tel_hrefs})
    phones = sorted({p for p in phones if p})
    addresses = []
    for line in text.split('|'):
        line = normalize_text(line)
        if len(line) > 10 and any(keyword in line for keyword in ADDRESS_KEYWORDS):
            addresses.append(line)
    addresses = sorted(dict.fromkeys(addresses))[:5]

    category_labels = []
    for term in CATEGORY_TERMS:
        if term in normalized_text:
            category_labels.append(term)
    category_labels = sorted(dict.fromkeys(category_labels), key=lambda x: CATEGORY_TERMS.index(x) if x in CATEGORY_TERMS else 999)

    generic_hints = [hint for hint in GENERIC_HINTS if hint in normalized_text]
    hero = ''
    if parser.headings:
        hero = parser.headings[0][1]

    page_data = {
        'directory': page_dir.name,
        'title': parser.title.strip(),
        'hero': hero,
        'headings': [h for _, h in parser.headings],
        'phones': phones,
        'addresses': addresses,
        'category_labels': category_labels,
        'generic_hints': generic_hints,
        'index_path': str(index_path),
        'has_meta': meta_path.exists(),
    }
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            meta = None
        page_data['meta'] = meta
        if meta:
            page_data['meta_phone'] = normalize_phone(meta.get('phone', ''))
            page_data['meta_address'] = normalize_text(meta.get('address', ''))
            page_data['meta_name'] = normalize_text(meta.get('name', ''))
            page_data['meta_category'] = normalize_text(meta.get('category', ''))
    else:
        page_data['meta'] = None
        page_data['meta_phone'] = ''
        page_data['meta_address'] = ''
        page_data['meta_name'] = ''
        page_data['meta_category'] = ''

    return page_data


def compare(page_data):
    results = {}
    results['directory'] = page_data['directory']
    results['title'] = page_data['title']
    results['hero'] = page_data['hero']
    results['phones'] = page_data['phones']
    results['addresses'] = page_data['addresses']
    results['category_labels'] = page_data['category_labels']
    results['generic_hints'] = page_data['generic_hints']
    results['meta'] = page_data['meta']
    results['meta_phone'] = page_data['meta_phone']
    results['meta_address'] = page_data['meta_address']
    results['meta_name'] = page_data['meta_name']
    results['meta_category'] = page_data['meta_category']

    results['phone_match'] = bool(page_data['meta_phone'] and page_data['meta_phone'] in ' '.join(page_data['phones']))
    results['address_match'] = bool(page_data['meta_address'] and any(page_data['meta_address'] in addr for addr in page_data['addresses']))
    results['name_match'] = bool(page_data['meta_name'] and (page_data['meta_name'] in normalize_text(page_data['title']) or page_data['meta_name'] in normalize_text(page_data['hero'])))
    results['category_match'] = bool(page_data['meta_category'] and page_data['meta_category'] in ' '.join(page_data['category_labels']))

    results['needs_review'] = not (results['phone_match'] and results['address_match'] and results['name_match'] and results['category_match']) or bool(results['generic_hints'])
    return results


def write_markdown(all_results):
    lines = [
        '# Audit report for local landing pages',
        '',
        'This report flags pages where the local preview may not match the business metadata or contains generic landing page copy.',
        '',
    ]
    for result in all_results:
        lines.extend([
            f'## {result["directory"]}',
            f'* Title: `{result["title"]}`',
            f'* Hero: `{result["hero"]}`',
            f'* Meta name: `{result["meta_name"]}`',
            f'* Meta category: `{result["meta_category"]}`',
            f'* Page categories: `{result["category_labels"]}`',
            f'* Page phones: `{result["phones"]}`',
            f'* Meta phone: `{result["meta_phone"]}`',
            f'* Page addresses: `{result["addresses"]}`',
            f'* Meta address: `{result["meta_address"]}`',
            f'* Generic hints: `{result["generic_hints"]}`',
            f'* Phone match: `{result["phone_match"]}`',
            f'* Address match: `{result["address_match"]}`',
            f'* Name/title match: `{result["name_match"]}`',
            f'* Category match: `{result["category_match"]}`',
            f'* Needs review: `{result["needs_review"]}`',
            '',
        ])
    OUTPUT_MD.write_text('\n'.join(lines), encoding='utf-8')


def main():
    page_dirs = [p for p in sorted(ROOT.iterdir()) if p.is_dir()]
    all_results = []
    flagged = []

    for page_dir in page_dirs:
        data = extract_page_data(page_dir)
        if not data:
            continue
        result = compare(data)
        all_results.append(result)
        if result['needs_review']:
            flagged.append(result['directory'])

    OUTPUT_JSON.write_text(json.dumps(all_results, indent=2, ensure_ascii=False), encoding='utf-8')
    write_markdown(all_results)
    FLAGGED.write_text('\n'.join(flagged), encoding='utf-8')
    print(f'Wrote {OUTPUT_JSON} and {OUTPUT_MD}')
    print(f'Flagged {len(flagged)} pages for review:')
    for item in flagged:
        print(f' - {item}')


if __name__ == '__main__':
    main()
