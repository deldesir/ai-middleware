import asyncio
import os
import sys
from litellm import completion
from dotenv import load_dotenv

# Load Env
load_dotenv("/opt/iiab/ai-middleware/.env")

full_key_string = os.getenv("GOOGLE_API_KEY", "")
keys = [k.strip() for k in full_key_string.split(",") if k.strip()]

MODEL = "gemini/gemini-2.0-flash"

async def test_key(index, key):
    masked = f"...{key[-6:]}"
    print(f"🔑 Testing Key #{index+1} ({masked}) with {MODEL}...", end=" ", flush=True)
    try:
        response = completion(
            model=MODEL,
            messages=[{"role": "user", "content": "Hi"}],
            api_key=key
        )
        print(f"✅ PASS")
        return True
    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False

async def main():
    if not keys:
        print("❌ No keys found in .env")
        return

    print(f"Found {len(keys)} keys.\n")
    
    results = []
    for i, key in enumerate(keys):
        req = await test_key(i, key)
        results.append(req)
        
    print("\n--- Summary ---")
    if all(results):
        print("✅ ALL KEYS WORKING")
    elif any(results):
        print("⚠️ PARTIAL FAILURE")
    else:
        print("❌ ALL KEYS FAILED")

if __name__ == "__main__":
    asyncio.run(main())
