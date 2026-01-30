import json
import logging
from google.genai import types
from app.services.llm_engine import generate_response_core
from app.database.repository import get_token, get_history, save_message, get_profile, save_profile
from app.core.config import get_api_keys

logger = logging.getLogger(__name__)

async def process_chat_request(db, phone_number, message, user_urn, groups):
    """
    Coordinator function that:
    1. Loads the Persona (Prompt + Tools)
    2. Loads Context (History + Profile)
    3. Calls Engine
    4. Executes Tools
    5. Saves State
    """
    
    # 1. Load Persona
    # For now, we only have the Default/Hardcoded Logic from the old llm.py
    # We will reconstruct it here as the "System Persona"
    
    repo_profile = await get_profile(user_urn)
    repo_token = await get_token(phone_number)
    
    # Construct System Prompt (Dynamic based on Persona)
    # TODO: Fetch from DB 'personas' table based on phone_number owner?
    # For the migration, we use the "KonexPro Master" logic if no specific persona found.
    
    is_subscriber = True if repo_token else False
    profile_str = json.dumps(repo_profile, indent=2) if repo_profile else "None"
    
    # Hardcoded "Master Persona" System Prompt (Legacy)
    # Logic: Usage of RapidPro Groups for conditions/restrictions
    # Example: "Premium" group gets checking tools, "Banned" gets nothing.
    group_list = ", ".join(groups) if groups else "None"
    is_premium = "Premium" in groups or "Beta" in groups
    
    # Construct System Prompt
    base_prompt = f"""
    You are Sarah, the AI Specialist at KonexPro.
    Your goal is to help businesses automate their customer service.
    
    ### 👤 USER CONTEXT
    * Status: {"✅ SUBSCRIBER" if is_subscriber else "❌ LEAD"}
    * Groups: {group_list}
    * Access Level: {"⭐ PREMIUM" if is_premium else "STANDARD"}
    * Known Profile: {profile_str}
    """
    
    # 2. Prepare Tools (Dynamic Gating)
    # We define the list of available tools.
    # We can restrict tools based on groups here.
    
    tool_declarations = [
        types.FunctionDeclaration(
            name="update_profile",
            description="Save user details to memory.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"data": types.Schema(type=types.Type.OBJECT)},
                required=["data"]
            )
        )
    ]

    # Condition: Only show payment link generator to non-subscribers or specific groups?
    # Or maybe only Premium users can generate links for others?
    # For now, we allow it for everyone, but note how we *could* restrict it:
    if True: # or "Sales" in groups:
        tool_declarations.append(
            types.FunctionDeclaration(
                name="generate_payment_link",
                description="create payment link",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={"plan_type": types.Schema(type=types.Type.STRING)},
                    required=["plan_type"]
                )
            )
        )

    tools = [
        types.Tool(function_declarations=tool_declarations),
        types.Tool(google_search=types.GoogleSearch())
    ]
    
    # 3. Check for Admin Mode
    # If the user is an admin, we override the persona and tools
    import os
    admin_phones = os.getenv("ADMIN_PHONES", "").split(",")
    is_admin = phone_number in admin_phones
    
    if is_admin:
        logger.warning(f"👑 Admin Mode Active for {phone_number}")
        base_prompt = """
        You are in GOD MODE.
        You have access to valid system tools.
        Use 'get_system_status' when asked for status.
        """
        tools.append(
            types.Tool(function_declarations=[
                types.FunctionDeclaration(
                    name="get_system_status",
                    description="Check database and cache health",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={}
                    )
                )
            ])
        )

    # 4. Call Engine
    chat_history = await get_history(user_urn)
    candidate_keys = get_api_keys(repo_token)
    
    # Save User Message first
    await save_message(user_urn, "user", message)
    
    response = await generate_response_core(
        base_prompt,
        chat_history,
        message,
        tools,
        candidate_keys
    )
    
    # 4. Handle Response & Tools
    reply_text = ""
    start_tool_exec = False
    
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.function_call:
                fname = part.function_call.name
                fargs = part.function_call.args
                logger.info(f"Using Tool: {fname}")
                
                if fname == "update_profile":
                    new_data = fargs.get("data", {})
                    repo_profile.update(new_data)
                    await save_profile(user_urn, repo_profile)
                    # Implicit acknowledgment or 2nd turn?
                    # For MVP refactor, we just accept it.
                    
                elif fname == "generate_payment_link":
                    # Logic...
                    pass

                elif fname == "get_system_status":
                     from app.database.connection import check_health as db_health
                     db_ok = await db_health()
                     reply_text = f"DB Status: {'OK' if db_ok else 'FAIL'}"
                     # In a real 2-turn ReAct, we would feed this back to LLM.
                     # For now, we append it to the reply.

            if part.text:
                reply_text += part.text
                
    if not reply_text:
        reply_text = "..." # Fallback
        
    # 5. Save Reply
    await save_message(user_urn, "assistant", reply_text)
    
    return reply_text
