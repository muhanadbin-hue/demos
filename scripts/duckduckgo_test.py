import urllib.request
import urllib.parse

query = 'CURLi by Lilian Macquarie Park'
url = 'https://html.duckduckgo.com/html/?q=' + urllib.parse.quote(query)
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=20) as resp:
    html = resp.read().decode('utf-8', errors='replace')
print(html[:2000])
