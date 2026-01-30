import httpx
import os
import logging
import json
import subprocess

logger = logging.getLogger(__name__)

WUZAPI_URL = os.getenv("WUZAPI_URL", "http://localhost:8080")
RAPIDPRO_URL = os.getenv("RAPIDPRO_URL", "http://localhost/rp")
RAPIDPRO_TOKEN = os.getenv("RAPIDPRO_TOKEN", "GJ3ZQ8HZEWZQUENXBQ9R8Z9LKSLJFXUYU6EYWZUN") 
MIDDLEWARE_PUBLIC_URL = os.getenv("MIDDLEWARE_PUBLIC_URL", "http://100.64.0.5:8001")

from temba_client.v2 import TembaClient

async def create_wuzapi_session(user_id: str):
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{WUZAPI_URL}/session/create",
            json={"sessionid": user_id},
            timeout=10
        )
        res.raise_for_status()
        return res.json()

async def get_wuzapi_qr(user_id: str):
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{WUZAPI_URL}/session/qr/{user_id}")
        if res.status_code == 200:
             return res.content 
        return None

async def get_wuzapi_pairing_code(user_id: str, phone_number: str):
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{WUZAPI_URL}/session/pairphone",
            json={"phone": phone_number, "sessionid": user_id},
            timeout=30
        )
        if res.status_code == 200:
            data = res.json()
            return data.get("LinkingCode") or data.get("data", {}).get("LinkingCode")
        return None

async def provision_channel_programmatically(phone_number: str):
    try:
        rpc_path = "/opt/iiab/rapidpro"
        rpc_python = "/home/iiab-admin/.cache/pypoetry/virtualenvs/temba-cUVkotcG-py3.12/bin/python"
        script_path = os.path.join(rpc_path, "manage_channels.py")
        cmd = [rpc_python, script_path, phone_number]
        
        process = subprocess.run(
            cmd, cwd=rpc_path, capture_output=True, text=True, check=False
        )
        
        if process.returncode != 0:
            logger.error(f"Provision Script Failed: {process.stderr}")
            return None
            
        lines = process.stdout.strip().split('\n')
        json_str = lines[-1] 
        return json.loads(json_str)

    except Exception as e:
        logger.error(f"Provisioning Error: {e}")
        return None

async def terminate_channel_programmatically(phone_number: str):
    try:
        rpc_path = "/opt/iiab/rapidpro"
        rpc_python = "/home/iiab-admin/.cache/pypoetry/virtualenvs/temba-cUVkotcG-py3.12/bin/python"
        script_path = os.path.join(rpc_path, "manage_channels.py")
        cmd = [rpc_python, script_path, phone_number, "--action", "terminate"]
        
        process = subprocess.run(
            cmd, cwd=rpc_path, capture_output=True, text=True, check=False
        )
        
        if process.returncode != 0:
            return None
            
        lines = process.stdout.strip().split('\n')
        json_str = lines[-1]
        return json.loads(json_str)

    except Exception as e:
        logger.error(f"Termination Error: {e}")
        return None

def get_rapidpro_client():
    return TembaClient(RAPIDPRO_URL, RAPIDPRO_TOKEN)

async def execute_rapidpro_intent(contact_urn: str, intent: str):
    """
    Executes an action based on intent.
    """
    clean_phone = contact_urn.split(":")[-1]
    logger.info(f"🤖 EXECUTING INTENT: {intent} for {contact_urn}")

    try:
        if intent == "SIGNUP":
            # Provision Channel Logic (Simplified)
            # In real system, call manage_channels.py via subprocess
            pass
            return True, f"\n\nLink: {MIDDLEWARE_PUBLIC_URL}/v1/qr/mock", {"qr_url": "mock"}

        elif intent == "STOP":
            return True, "", {"opt_out": True}

        elif intent == "TERMINATE":
            return True, "", {"terminated": True}
            
    except Exception as e:
        logger.error(f"❌ RapidPro Action Failed: {e}")
        return False, " (System Error)", {}
    
    return True, "", {} 
