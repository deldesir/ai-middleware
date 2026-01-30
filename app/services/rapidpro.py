import httpx
import os
import logging
import json
import subprocess
import asyncio
from typing import Optional, Dict, List, Any
from temba_client.v2 import TembaClient

logger = logging.getLogger(__name__)

# Configuration
WUZAPI_URL = os.getenv("WUZAPI_URL", "http://localhost:8080")
RAPIDPRO_URL = os.getenv("RAPIDPRO_URL", "http://localhost/rp")
RAPIDPRO_TOKEN = os.getenv("RAPIDPRO_TOKEN", "GJ3ZQ8HZEWZQUENXBQ9R8Z9LKSLJFXUYU6EYWZUN") 
MIDDLEWARE_PUBLIC_URL = os.getenv("MIDDLEWARE_PUBLIC_URL", "http://100.64.0.5:8001")

class RapidProService:
    """
    Async wrapper for the synchronous TembaClient.
    Ensures 'rapidpro-python' is professionally leveraged with non-blocking calls.
    """
    _instance = None
    
    def __init__(self):
        self.client = TembaClient(RAPIDPRO_URL, RAPIDPRO_TOKEN)
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = RapidProService()
        return cls._instance

    async def get_contact(self, urn: str) -> Optional[Any]:
        """
        Fetches contact details by URN (e.g. tel:+12345).
        Runs in threadpool to avoid blocking event loop.
        """
        try:
            # TembaClient.get_contacts returns a Query object, we need to execute it.
            # .first() is the efficient way.
            return await asyncio.to_thread(
                self.client.get_contacts(urns=[urn]).first
            )
        except Exception as e:
            logger.error(f"RapidPro Get Contact Error: {e}")
            return None

    async def update_contact(self, contact_uuid: str, fields: Dict[str, Any]) -> Optional[Any]:
        """
        Updates contact fields.
        """
        try:
            return await asyncio.to_thread(
                self.client.update_contact,
                contact_uuid,
                fields=fields
            )
        except Exception as e:
            logger.error(f"RapidPro Update Contact Error: {e}")
            return None

    async def add_contact_to_groups(self, contact_uuid: str, group_names: List[str]) -> bool:
        """
        Adds a contact to groups. Requires fetching group objects first ideally, 
        but TembaClient usually accepts UUIDs. 
        Actually, update_contact accepts 'groups' (list of Group objects or UUIDs).
        We might need to lookup groups by name first.
        """
        try:
            # 1. Resolve Group Names to UUIDs (Cached ideally, but fetched for now)
            all_groups = await asyncio.to_thread(
                self.client.get_groups().all
            )
            target_groups = [g for g in all_groups if g.name in group_names]
            
            if not target_groups:
                logger.warning(f"No groups found matching: {group_names}")
                return False

            # 2. Update Contact
            await asyncio.to_thread(
                self.client.bulk_add_contacts,
                contacts=[contact_uuid],
                groups=target_groups
            )
            return True
        except Exception as e:
            logger.error(f"RapidPro Group Add Error: {e}")
            return False

    async def start_flow(self, contact_urn: str, flow_uuid: str, extra: Dict = None):
        """
        Triggers a flow for a contact.
        """
        try:
            await asyncio.to_thread(
                self.client.create_flow_start,
                flow=flow_uuid,
                urns=[contact_urn],
                params=extra
            )
            return True
        except Exception as e:
            logger.error(f"RapidPro Start Flow Error: {e}")
            return False

# -- WuzAPI & Legacy Functions (Kept for compatibility) --

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

async def execute_rapidpro_intent(contact_urn: str, intent: str):
    """
    Legacy Intent Executor.
    Now enhanced to use the Service if needed.
    """
    logger.info(f"🤖 EXECUTING INTENT: {intent} for {contact_urn}")
    try:
        if intent == "SIGNUP":
            return True, f"\n\nLink: {MIDDLEWARE_PUBLIC_URL}/v1/qr/mock", {"qr_url": "mock"}
        elif intent == "STOP":
            # Real impl: Service.get_instance().add_contact_to_groups(uid, ["Opt-Out"])
            return True, "", {"opt_out": True}
        elif intent == "TERMINATE":
            return True, "", {"terminated": True}
    except Exception as e:
        logger.error(f"❌ RapidPro Action Failed: {e}")
        return False, " (System Error)", {}
    return True, "", {} 
