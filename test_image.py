"""
Debug: print the actual Pollinations response body for HTTP 500 to understand the error.
"""
import requests, urllib.parse

prompt = "a white cat"
encoded = urllib.parse.quote(prompt)
url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&model=flux&nologo=true"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

print(f"URL: {url}")
r = requests.get(url, headers=headers, timeout=30)
print(f"Status: {r.status_code}")
print(f"Content-Type: {r.headers.get('Content-Type', 'unknown')}")
print(f"Body (first 500 chars): {r.text[:500]}")
print(f"First bytes hex: {r.content[:40].hex()}")

# Test without model param
print("\n--- Without model param ---")
url2 = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512"
r2 = requests.get(url2, headers=headers, timeout=30)
print(f"Status: {r2.status_code}")
print(f"Content-Type: {r2.headers.get('Content-Type', 'unknown')}")
print(f"Body (first 200 chars): {r2.text[:200]}")

# Test minimal URL
print("\n--- Minimal URL ---")
url3 = f"https://image.pollinations.ai/prompt/{encoded}"
r3 = requests.get(url3, headers={"User-Agent": "curl/7.64.1"}, timeout=30)
print(f"Status: {r3.status_code}")
print(f"Content-Type: {r3.headers.get('Content-Type', 'unknown')}")
is_img = r3.content[:4] in [b'\xff\xd8\xff\xe0', b'\xff\xd8\xff\xe1', b'\x89PNG', b'GIF8']
print(f"Looks like image: {is_img}, Size: {len(r3.content)} bytes")
