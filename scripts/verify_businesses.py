import argparse
import html
import json
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

SEARCH_URL = 'https://html.duckduckgo.com/html/?q='
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://duckduckgo.com/',
}

PHONE_RE = re.compile(r'0[23478][\d\s\-\(\)]{6,}')
ADDRESS_RE = re.compile(r'\b\d{1,4}[A-Za-z]?\s+(?:[A-Z][a-z]+\s+){1,6}(?:Rd|Road|St|Street|Ave|Avenue|Ln|Lane|Dr|Drive|Blvd|Boulevard|Terrace|Tce|Court|Ct|Place|Pl|Square|Sq|Cres|Crescent|Parade|Pde|Way)\b', re.I)

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.texts = []

    def handle_data(self, data):
        self.texts.append(data)

    def get_text(self):
        return ' '.join(self.texts)


def fetch_search_html(query, retries=3):
    url = SEARCH_URL + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers=HEADERS)
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code in (403, 429) and attempt < retries:
                delay = 1.5 + random.random()
                time.sleep(delay)
                continue
            raise RuntimeError(f'HTTP {exc.code} for query {query}') from exc
        except urllib.error.URLError as exc:
            last_exc = exc
            if attempt < retries:
                delay = 1.5 + random.random()
                time.sleep(delay)
                continue
            raise RuntimeError(f'URL error for query {query}: {exc}') from exc
    raise RuntimeError(f'Failed to fetch query {query}: {last_exc}')


def html_to_text(html_str):
    parser = TextExtractor()
    parser.feed(html_str)
    return parser.get_text()


def normalize_text(value):
    if not value:
        return ''
    value = html.unescape(value)
    value = value.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    return re.sub(r'\s+', ' ', value).strip().lower()


def extract_supporting_data(text):
    normalized = normalize_text(text)
    phones = {re.sub(r'\D', '', m) for m in PHONE_RE.findall(text)}
    addresses = {m.strip() for m in ADDRESS_RE.findall(text)}
    return normalized, phones, addresses


def compare_page(page, retries=3):
    query = page['query']
    text = html_to_text(fetch_search_html(query, retries=retries))
    normalized, found_phones, found_addresses = extract_supporting_data(text)

    expected_title = normalize_text(page['title'])
    expected_name = normalize_text(query)
    expected_addresses = [normalize_text(addr) for addr in page.get('expected_addresses', []) if addr]
    expected_phones = {re.sub(r'\D', '', p) for p in page.get('phones', []) if p}

    name_match = expected_name in normalized or expected_name.split(' ')[0] in normalized
    title_match = expected_title in normalized
    address_match = any(addr in normalized for addr in expected_addresses if addr)
    phone_match = any(phone in normalized for phone in expected_phones if phone)

    search_summary = []
    if found_addresses:
        search_summary.append('Found addresses: ' + ', '.join(sorted(found_addresses)))
    if found_phones:
        search_summary.append('Found phones: ' + ', '.join(sorted(found_phones)))
    search_summary.append('Matched name: ' + str(name_match))
    search_summary.append('Matched title: ' + str(title_match))
    search_summary.append('Matched expected address: ' + str(address_match))
    search_summary.append('Matched expected phone: ' + str(phone_match))

    return {
        'directory': page['directory'],
        'query': query,
        'title': page['title'],
        'expected_addresses': page.get('expected_addresses', []),
        'phones': page.get('phones', []),
        'search_summary': ' | '.join(search_summary),
        'address_match': address_match,
        'phone_match': phone_match,
        'name_match': name_match,
        'title_match': title_match,
        'found_addresses': sorted(found_addresses),
        'found_phones': sorted(found_phones),
    }


def write_markdown(results, path):
    lines = [
        '# Business verification results',
        '',
        'This file lists pages where the local page content did not clearly match search engine results.',
        '',
    ]
    for result in results:
        lines.extend([
            f'## {result["directory"]}',
            f'* Query: `{result["query"]}`',
            f'* Local title: `{result["title"]}`',
            f'* Expected addresses: {result["expected_addresses"]}',
            f'* Expected phones: {result["phones"]}',
            f'* Search summary: {result["search_summary"]}',
            f'* Found addresses: {result["found_addresses"]}',
            f'* Found phones: {result["found_phones"]}',
            f'* Needs review: `{not (result["address_match"] or result["phone_match"] or result["title_match"])}`',
            '',
        ])
    path.write_text('\n'.join(lines), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description='Verify local page metadata against search results.')
    parser.add_argument('--start', type=int, default=0, help='Start index for verification (0-based).')
    parser.add_argument('--end', type=int, default=None, help='End index for verification (exclusive).')
    parser.add_argument('--limit', type=int, default=None, help='Limit how many pages to verify.')
    parser.add_argument('--delay', type=float, default=1.2, help='Delay in seconds between queries.')
    parser.add_argument('--retries', type=int, default=3, help='Number of retry attempts for failing requests.')
    parser.add_argument('--output', default='scripts/change_list.md', help='Markdown result output path.')
    parser.add_argument('--source', default='scripts/query_list.json', help='Source JSON with query metadata.')
    args = parser.parse_args()

    queries = json.loads(Path(args.source).read_text(encoding='utf-8'))
    start = args.start
    end = args.end if args.end is not None else len(queries)
    results = []
    for idx, page in enumerate(queries[start:end], start=start):
        if args.limit and idx - start >= args.limit:
            break
        print(f'[{idx+1}/{len(queries)}] Verifying {page["directory"]}...')
        try:
            result = compare_page(page, retries=args.retries)
        except Exception as exc:
            print(f'  ERROR: {exc}')
            result = {
                'directory': page['directory'],
                'query': page['query'],
                'title': page['title'],
                'expected_addresses': page.get('expected_addresses', []),
                'phones': page.get('phones', []),
                'search_summary': f'ERROR: {exc}',
                'address_match': False,
                'phone_match': False,
                'name_match': False,
                'title_match': False,
                'found_addresses': [],
                'found_phones': [],
            }
        results.append(result)
        if idx < end - 1:
            time.sleep(args.delay)

    write_markdown(results, Path(args.output))
    print(f'Wrote verification results to {args.output}')


if __name__ == '__main__':
    main()
