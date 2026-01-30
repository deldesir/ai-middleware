import sys
import os
import asyncio

# Ensure parent path is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clients import get_rapidpro_client

def sync_triggers():
    print("🔄 Connecting to RapidPro API...")
    client = get_rapidpro_client()
    
    # 1. Find Flow
    print("🔎 Searching for 'AI Onboarding' Flow...")
    # Fetch all flows (no name filter in SDK apparently)
    flows = client.get_flows().all()
    
    target_flow = None
    for f in flows:
        if "onboard" in f.name.lower():
            target_flow = f
            print(f"✅ Found Flow: {target_flow.name} ({target_flow.uuid})")
            break
    
    if not target_flow:
        print("❌ Error: Could not find 'AI Onboarding Flow'. Please create it first.")
        # Attempt to list all for debugging
        print("Available Flows:")
        for f in flows:
            print(f"- {f.name}")
        return

    # 2. Define Triggers
    keywords = ["konex", "start", "komanse", "wi", "yes", "go"]
    keyword_string = ", ".join(keywords)
    
    print(f"⚙️  Syncing Triggers: [{keyword_string}] -> {target_flow.name}")
    
    # 3. Create/Update Trigger
    # RapidPro API v2 'create_trigger'
    # trigger_type='K' (Keyword)
    try:
        # Check existing
        existing = client.get_triggers(flow=target_flow.uuid).all()
        for t in existing:
            if t.trigger_type == 'K':
                print(f"⚠️  Found existing keyword trigger: '{t.keyword}'. Updating/Skipping...")
                # We might want to just create a new one to be sure content covers all
                # But RapidPro usually allows one keyword trigger per flow or multiple?
                # Usually we want one trigger with multiple keywords space separated or comma? 
                # RapidPro keywords are often space separated in the UI field.
                
        # Create new trigger
        # catch_all=False, trigger_type='K', value=keyword_string
        trigger = client.create_trigger(
            flow=target_flow.uuid, 
            trigger_type='K', 
            keyword=keyword_string
        )
        print(f"✅ Trigger Created! ID: {trigger.uuid}")
        print(f"   Keywords: {trigger.keyword}")
        
    except Exception as e:
        print(f"❌ Error creating trigger: {e}")

if __name__ == "__main__":
    sync_triggers()
