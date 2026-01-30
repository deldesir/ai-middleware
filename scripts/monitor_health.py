import httpx
import sys

URL = "http://localhost:8001/health"

def check():
    try:
        r = httpx.get(URL, timeout=5)
        if r.status_code == 200:
            data = r.json()
            # Optional: Check deep status
            if data.get("status") == "ok":
                print(f"✅ AI Middleware ONLINE. (DB: {data['checks']['database']}, Valkey: {data['checks']['valkey']})")
                sys.exit(0)
            else:
                 print(f"⚠️ Service DEGRADED: {data}")
                 sys.exit(1)
        else:
            print(f"❌ Service HTTP Error: {r.status_code}")
            print(r.text)
            sys.exit(1)
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check()
