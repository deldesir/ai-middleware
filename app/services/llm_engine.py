from google import genai
from google.genai import types
import logging
import os
import traceback
import asyncio
import time

logger = logging.getLogger(__name__)

# --- Key Rotation Logic ---
async def _call_llm_safe_rotation(messages, tools, model, candidate_keys, cooldown_seconds=60):
    # This logic remains the same as verified before, just ensuring imports are correct
    # We might need to inject the cache/failure marking dependency or keep it self-contained
    # For refactor, let's keep it here but we need 'mark_key_failure'
    # We can import it from app.services.cache (if we move it) or keep using cache.py for now
    
    # Ideally, cache logic moves to app/services/cache.py
    # For now, let's assume we import the old one or move it.
    # Plan: Move cache.py to app/services/cache.py
    from app.services.cache import mark_key_failure 
    
    config = types.GenerateContentConfig(
        tools=tools,
        system_instruction=messages[0].parts[0].text if messages[0].role == "system" else None,
        temperature=0.7
    )
    
    # Filter out system message from 'contents'
    content_payload = [m for m in messages if m.role != "system"]

    for i, access_token in enumerate(candidate_keys):
        try:
            client = genai.Client(api_key=access_token)
            response = client.models.generate_content(
                model=model,
                contents=content_payload,
                config=config
            )
            return response
        except Exception as e:
            error_str = str(e).lower()
            is_rate_limit = any(x in error_str for x in ["429", "quota", "503", "overloaded"])
            if is_rate_limit:
                 cooldown = cooldown_seconds if "503" not in error_str else 2
                 logger.warning(f"⚠️ Key #{i+1} Failed. Cooldown {cooldown}s.")
                 await mark_key_failure(access_token, cooldown)
                 continue 
            raise e
    raise Exception("All keys exhausted")


async def generate_response_core(
    system_prompt: str,
    chat_history: list,
    user_message: str,
    tools: list,
    candidate_keys: list,
    model: str = "gemini-3-flash-preview"
):
    """
    Pure Engine Function:
    Input: Context, Tools, Configuration
    Output: Reply Text, Intent, Metadata
    """
    
    # Construct Messages
    system_message = types.Content(role="system", parts=[types.Part.from_text(text=system_prompt)])
    
    formatted_history = []
    for msg in chat_history:
        formatted_history.append(types.Content(
            role="model" if msg["role"] == "assistant" else "user",
            parts=[types.Part.from_text(text=msg["content"])]
        ))
        
    new_user_message = types.Content(role="user", parts=[types.Part.from_text(text=user_message)])
    
    full_contents = [system_message] + formatted_history + [new_user_message]
    
    reply_text = ""
    final_intent = None
    final_metadata = {}
    
    try:
        # Turn 1
        response = await _call_llm_safe_rotation(full_contents, tools, model, candidate_keys)
        
        executed_tool = False
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    executed_tool = True
                    fname = part.function_call.name
                    fargs = part.function_call.args
                    
                    # We return the Tool Call so the Caller (Manager) can execute it?
                    # Or we execute it here?
                    
                    # Better Architecture: The Engine executes "Prompt -> Thought".
                    # If Thought is "Call Tool", we return that instruction.
                    # The Service Layer executes the tool (DB, API).
                    # Then we optionally loop back.
                    
                    # For this refactor, to keep it simple but modular:
                    # We will return the raw result and let the 'PersonaManager' handle execution loops.
                    # BUT that makes multi-turn hard (re-calling the engine).
                    
                    # COMPROMISE: We handle "System Tools" (Profile) here or stick to the previous pattern?
                    # Let's return the simplified structure: List of ToolCalls to be executed.
                    
                    # Actually, sticking to the "Manager" pattern:
                    # The Engine should just return the Response Object.
                    return response 
                    
        # If just text
        return response

    except Exception as e:
        logger.error(f"Engine Error: {e}")
        raise e
