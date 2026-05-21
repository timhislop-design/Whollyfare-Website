"""
find_kroger_store.py — one-time helper to find your Kroger location ID.
Run from the repo root: python find_kroger_store.py
Delete this file once you have the ID in your .env.
"""
import sys
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("ERROR: python-dotenv not installed. Run: pip install python-dotenv")
    sys.exit(1)

try:
    from integrations.kroger.client import KrogerClient
except ImportError as e:
    print(f"ERROR: could not import KrogerClient: {e}")
    print("Make sure you're running from the Whollyfare-Website folder.")
    sys.exit(1)

client_id     = os.environ.get("KROGER_CLIENT_ID", "")
client_secret = os.environ.get("KROGER_CLIENT_SECRET", "")

if not client_id or not client_secret:
    print("ERROR: KROGER_CLIENT_ID or KROGER_CLIENT_SECRET not found.")
    print("Check that your .env file exists in this folder.")
    sys.exit(1)

print(f"Using client_id: {client_id}")
print("Connecting to Kroger API...\n")

try:
    client = KrogerClient(client_id=client_id, client_secret=client_secret)
    stores = client.find_stores(zip_code="22903", radius_miles=15, limit=10)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

if not stores:
    print("No stores found near 22903.")
    sys.exit(1)

print(f"{'Location ID':<14} {'Name':<30} {'Address':<45} {'Miles':>5}")
print("-" * 100)
for s in stores:
    print(f"{s['locationId']:<14} {s['name']:<30} {s['address']:<45} {s['distance_mi']:>5}")

print("\nCopy the locationId for Barracks Road into your .env:")
print("  KROGER_LOCATION_ID=<paste it here>")
