"""
diagnose.py — Flipp endpoint diagnostic
Run from project root:  python integrations/flipp/diagnose.py --zip 22963

Tries every known Flipp API endpoint variant and reports exactly what
each one returns (status code, content-type, body preview).
Use the output to identify which URL is currently active.
"""
import json, sys
from urllib import request, error

ZIP = "22963"
if "--zip" in sys.argv:
    i = sys.argv.index("--zip")
    ZIP = sys.argv[i+1]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "identity",      # no compression — keeps body readable
    "Referer":         "https://flipp.com/",
    "Origin":          "https://flipp.com",
    "X-Requested-With": "XMLHttpRequest",
}

CANDIDATES = [
    f"https://flipp.com/flyers.json?locale=en-US&postal_code={ZIP}",
    f"https://flipp.com/api/flyers?locale=en-US&postal_code={ZIP}",
    f"https://flipp.com/api/2/publications.json?locale=en-US&postal_code={ZIP}",
    f"https://dam.flippenterprise.net/flyerkit/publications?locale=en-US&postal_code={ZIP}&access_token=a3e4181c47f1d21998a49e1f9e9888bc",
    f"https://dam.flippenterprise.net/flyerkit/publications?locale=en-US&postal_code={ZIP}&access_token=b64ecad54f8e18f4a62bc7c5a9284f54",
]

def probe(url):
    req = request.Request(url, headers=HEADERS)
    try:
        with request.urlopen(req, timeout=15) as resp:
            status  = resp.status
            ct      = resp.headers.get("Content-Type", "?")
            raw     = resp.read()
            decoded = raw.decode("utf-8", errors="replace")
            is_json = False
            count   = 0
            try:
                data = json.loads(decoded)
                is_json = True
                count = len(data) if isinstance(data, list) else (
                    len(data.get("flyers", data.get("publications", [])))
                )
            except Exception:
                pass
            return status, ct, len(raw), decoded[:300], is_json, count
    except error.HTTPError as e:
        return e.code, str(e), 0, f"HTTP error: {e.reason}", False, 0
    except error.URLError as e:
        return 0, "URLError", 0, str(e.reason), False, 0

print(f"\nFlipp endpoint diagnostic — zip {ZIP}")
print("=" * 70)
for url in CANDIDATES:
    print(f"\n▶ {url[:80]}")
    status, ct, blen, preview, is_json, count = probe(url)
    if is_json:
        print(f"  ✅ STATUS {status} | {ct} | {blen} bytes | JSON ✓ | {count} items")
    else:
        print(f"  ❌ STATUS {status} | {ct} | {blen} bytes | not JSON")
        print(f"  Body: {repr(preview[:200])}")
