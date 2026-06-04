import urllib.request
import urllib.parse
import re

query = 'CURLi by Lilian Macquarie Park'
url = 'https://html.duckduckgo.com/html/?q=' + urllib.parse.quote(query)
headers = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Referer': 'https://duckduckgo.com/',
}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=20) as resp:
    html = resp.read().decode('utf-8', errors='replace')

print('len', len(html))
print('title:', re.search(r'<title>(.*?)</title>', html, re.I | re.S).group(1).strip() if re.search(r'<title>(.*?)</title>', html, re.I | re.S) else 'NONE')
print('has result class:', bool(re.search(r'class=["\'].*?result.*?["\']', html)))
print('has link:', 'href="' in html[:4000])
print('snippet:')
start = html.find('<div class="results">')
if start >= 0:
    print(html[start:start+1000])
else:
    print(html[:1000])
