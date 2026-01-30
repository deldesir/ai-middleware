import asyncio
import os
import sys

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm import generate_response
from services import FakeDatabaseService
from db import init_db

async def test_llm_behavior():
    print("Testing LLM Tool Call Behavior...")
    
    # Fake DB
    fake_db = FakeDatabaseService()
    
    # Simulated User Input
    phone = "50912345678"
    message = "Start" # Trigger for Cleanup/Signup
    
    print(f"User: {message}")
    
    # We call generate_response directly
    # Note: We rely on the REAL generate_response logic which uses litellm
    # We need to ensure we have credentials in .env or local execution
    
    from dotenv import load_dotenv
    load_dotenv()
    
    response, intent, meta = await generate_response(
        db=fake_db,
        phone_number=phone,
        message=message,
        # model="gemini/gemini-1.5-flash", # Use default
        user_urn="whatsapp:50912345678"
    )
    
    print(f"Response: {response}")
    print(f"Intent: {intent}")
    print(f"Meta: {meta}")

# Direct MonCash Simulation Test
print("\n[Direct Test] MonCash Simulation:")
from moncash import MonCashClient
import time
client = MonCashClient()
link = client.create_payment("TEST-ORDER", 1000)
print(f"Generate Link: {link}")
if "mock/pay" in link:
    print("✅ SIMULATION MODE ACTIVE")
else:
    print("❌ WARNING: REAL URL GENERATED")

    # Only run LLM if we want to (it crashes now)
    # asyncio.run(test_llm_behavior())
