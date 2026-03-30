import requests, urllib.parse
p = 'cat hacker'
url = f'https://image.pollinations.ai/prompt/{urllib.parse.quote(p)}?model=flux'
try:
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
    print('Poll Code:', r.status_code)
    print('Poll is_html:', r.content.startswith(b'<!DOCTYPE') or r.content.startswith(b'<html'))
except Exception as e:
    print('Poll error:', e)

af_url = f'https://api.airforce/v1/imagine2?prompt={urllib.parse.quote(p)}'
try:
    r2 = requests.get(af_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
    print('AF Code:', r2.status_code)
    print('AF is_html:', r2.content.startswith(b'<!DOCTYPE') or r2.content.startswith(b'<html'))
except Exception as e:
    print('AF Error:', e)
