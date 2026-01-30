import asyncio
import os
import sys
from litellm import completion
from dotenv import load_dotenv

# Load Env
load_dotenv("/opt/iiab/ai-middleware/.env")

# Get Key (Prioritize local_vars logic if needed, but .env is simpler for script)
# We need to make sure we use a valid key.
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ GOOGLE_API_KEY not found in environment.")
    sys.exit(1)

# Handle CSV keys
if "," in api_key:
    api_key = api_key.split(",")[0].strip()

MODELS_TO_TEST = [
    "gemini/gemini-1.5-flash",
    "gemini/gemini-2.0-flash-exp", 
    "gemini/gemini-3.0-flash-preview", # The one in question
    "gemini/gemini-pro"
]

async def test_model(model_name):
    print(f"Testing {model_name}...", end=" ", flush=True)
    try:
        response = completion(
            model=model_name,
            messages=[{"role": "user", "content": "Hi"}],
            api_key=api_key
        )
        print(f"✅ SUCCESS")
        return True
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

async def main():
    print(f"🔑 Testing with Key: ...{api_key[-6:]}")
    
    results = {}
    for model in MODELS_TO_TEST:
        results[model] = await test_model(model)
        
    print("\n--- Summary ---")
    for m, status in results.items():
        print(f"{m}: {'OPEN' if status else 'CLOSED/INVALID'}")

if __name__ == "__main__":
    asyncio.run(main())
