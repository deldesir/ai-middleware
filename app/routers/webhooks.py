from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from app.personas.manager import process_chat_request
from app.database.repository import record_payment
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    message = data.get("text", "")
    user_urn = data.get("user") # e.g. telegram:12345
    groups = data.get("groups", [])
    
    # RapidPro might send us URNs like tel:+509...
    # We extract the clean phone number for Owner Logic
    phone_number = user_urn.split(":")[-1] if user_urn else "anon"
    
    # We process in background if we want to return 200 OK fast to RapidPro?
    # Actually RapidPro waits for the response to stick in the flow usually.
    # So we await it.
    
    # Mock DB dependency via "from app.database.connection..." inside sub-functions for now
    # Ideally use FastAPI Dependency Injection
    
    reply = await process_chat_request(None, phone_number, message, user_urn, groups)
    
    return {
        "text": reply,
        "intent": "REPLIED" # Simplified for MVP
    }

@router.post("/hooks/sms")
async def sms_hook(request: Request):
    """
    Receives SMS JSON from Android Tasker.
    Payload: { "sender": "...", "body": "...", "timestamp": ... }
    Header: X-SMS-Secret matches env var
    """
    secret = request.headers.get("X-SMS-Secret")
    expected = os.getenv("SMS_SECRET", "changeme")
    
    if secret != expected:
        return JSONResponse(status_code=403, content={"error": "Invalid Secret"})
        
    data = await request.json()
    sender = data.get("sender")
    body = data.get("body")
    
    if not body:
        return {"status": "ignored", "reason": "no_body"}
        
    # Parse
    from app.services.parsers import parse_payment_sms
    parsed = parse_payment_sms(body, sender)
    
    if parsed and parsed["code"]:
        await record_payment(
            code=parsed["code"],
            amount=parsed["amount"],
            currency=parsed["currency"],
            sender=parsed["sender"],
            raw_message=body
        )
        logger.info(f"💰 Payment Recorded: {parsed['code']} ({parsed['amount']} {parsed['currency']})")
        return {"status": "recorded", "code": parsed["code"]}
        
    return {"status": "ignored", "reason": "no_code_found"}

@router.get("/qr/{session_id}")
async def proxy_qr(session_id: str):
    """
    Proxies the QR code from WuzAPI so RapidPro can consume it as an image URL.
    """
    from fastapi.responses import Response
    from app.services.rapidpro import get_wuzapi_qr, create_wuzapi_session
    
    # 1. Ensure Session Exists (Idempotent)
    try:
        await create_wuzapi_session(session_id)
    except Exception as e:
        logger.warning(f"Session Create Warning: {e}")
        
    # 2. Fetch QR
    qr_bytes = await get_wuzapi_qr(session_id)
    
    if qr_bytes:
        return Response(content=qr_bytes, media_type="image/png")
    else:
        return Response(content=b"QR Not Found", status_code=404)
