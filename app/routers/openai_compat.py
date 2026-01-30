from fastapi import APIRouter, Request, HTTPException
from app.personas.manager import process_chat_request
import logging
import time
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/v1/chat/completions")
async def openai_chat_completions(request: Request):
    """
    OpenAI-compatible endpoint for RapidPro's "LLM" channel type.
    Redirects the last user message to our internal logic.
    """
    try:
        data = await request.json()
        messages = data.get("messages", [])
        
        if not messages:
            raise HTTPException(status_code=400, detail="No messages provided")
            
        # Extract the last user message
        # RapidPro typically sends the full history, but our internal logic
        # fetches history from DB. We just need the *new* trigger.
        last_user_msg = next((m for m in reversed(messages) if m["role"] == "user"), None)
        
        if not last_user_msg:
             # Fallback if only system?
             content = "Hello"
        else:
             content = last_user_msg.get("content", "")

        # Extract User ID if possible (OpenAI doesn't strictly have this in body)
        # We might look for a 'user' field in the body (optional in OpenAI spec)
        user_id = data.get("user", "anon_openai")
        
        # Phone Logic extraction
        # If the user_id from RapidPro format is like "tel:+123", we parse it.
        phone_number = user_id.split(":")[-1] if ":" in user_id else user_id
        
        # Groups? OpenAI spec doesn't support generic metadata easily.
        # We'll assume empty groups for this compatibility mode unless passed in specific headers?
        # For now, MVP: No groups logic for OpenAI endpoint.
        groups = []

        logger.info(f"OpenAI Compat Request from {user_id}: {content}")

        # Call Internal Logic
        reply_text = await process_chat_request(None, phone_number, content, user_id, groups)
        
        # Format Response as OpenAI Object
        return {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": data.get("model", "konex-ai"),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": reply_text
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": len(content), 
                "completion_tokens": len(reply_text),
                "total_tokens": len(content) + len(reply_text)
            }
        }
        
    except Exception as e:
        logger.error(f"OpenAI Compat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
