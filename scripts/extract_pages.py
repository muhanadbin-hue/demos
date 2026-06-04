import json
from pathlib import Path
import re
from html.parser import HTMLParser

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.texts = []
    def handle_data(self, data):
        self.texts.append(data)
    def get_text(self):
        return "|".join(self.texts)

root = Path('docs')
pages = []
for item in sorted(root.iterdir()):
    if item.is_dir():
        html_path = item / 'index.html'
        if html_path.exists():
            html = html_path.read_text(encoding='utf-8')
            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else ''
            html_clean = re.sub(r'<script[\s\S]*?<\/script>', '', html, flags=re.IGNORECASE)
            html_clean = re.sub(r'<style[\s\S]*?<\/style>', '', html_clean, flags=re.IGNORECASE)
            parser = TextExtractor()
            parser.feed(html_clean)
            text = parser.get_text()
            phones = re.findall(r'0[23478]\d[\d\s\-\(\)]{6,}', text)
            phones = [re.sub(r'\D', '', p) for p in phones]
            addresses = []
            for line in text.split('|'):
                line = line.strip()
                if len(line) > 5 and ('NSW' in line or 'Australia' in line or 'Rd' in line or 'St' in line):
                    addresses.append(line)
            pages.append({
                'directory': item.name,
                'title': title,
                'phones': phones,
                'addresses': addresses[:3]
            })

Path('scripts/page_metadata.json').write_text(json.dumps(pages, indent=2, ensure_ascii=False), encoding='utf-8')
output_lines = []
for page in pages:
    output_lines.append(page['directory'])
    output_lines.append(f"  title: {page['title']}")
    output_lines.append(f"  phones: {page['phones']}")
    output_lines.append(f"  addresses: {page['addresses']}")
output = '\n'.join(output_lines)
Path('scripts/page_metadata.txt').write_text(output, encoding='utf-8')
print('Wrote metadata to scripts/page_metadata.txt and scripts/page_metadata.json')
