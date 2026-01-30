import json
from app.database.connection import get_db_connection

# --- User Tokens Repository ---
async def get_token(phone_number: str):
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM ai_tokens WHERE phone_number = $1", phone_number)
        return dict(row) if row else None
    finally:
        await conn.close()

# --- Chat History Repository ---
async def get_history(user_id: str, limit: int = 10):
    conn = await get_db_connection()
    try:
        # Fetch last N messages
        # Note: We likely want them in chronological order for the LLM
        rows = await conn.fetch("""
            SELECT role, content FROM (
                SELECT role, content, created_at FROM chat_sessions 
                WHERE user_id = $1 
                ORDER BY created_at DESC 
                LIMIT $2
            ) sub ORDER BY created_at ASC
        """, user_id, limit)
        return [dict(role=r["role"], content=r["content"]) for r in rows]
    finally:
        await conn.close()

async def save_message(user_id: str, role: str, content: str):
    conn = await get_db_connection()
    try:
        await conn.execute(
            "INSERT INTO chat_sessions (user_id, role, content) VALUES ($1, $2, $3)",
            user_id, role, content
        )
        return True
    finally:
        await conn.close()

# --- Semantic Profile Repository ---
async def get_profile(user_id: str):
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("SELECT profile_data FROM user_profile WHERE user_id = $1", user_id)
        return dict(row["profile_data"]) if row and row["profile_data"] else {}
    except Exception:
        return {} 
    finally:
        await conn.close()

async def save_profile(user_id: str, profile_data: dict):
    conn = await get_db_connection()
    try:
        json_data = json.dumps(profile_data)
        await conn.execute("""
            INSERT INTO user_profile (user_id, profile_data, updated_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (user_id) DO UPDATE SET
                profile_data = $2,
                updated_at = NOW();
        """, user_id, json_data)
    finally:
        await conn.close()

# --- Personas Repository (New) ---
async def get_persona(persona_id: str):
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM personas WHERE id = $1", persona_id)
        return dict(row) if row else None
    finally:
        await conn.close()
        
async def get_default_persona():
    # Returns the "Master Bot" or default config
    # For now, if no table exists or no row, we return a hardcoded fallback or None
    # Ideally we fetch the row marked 'is_default'
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM personas WHERE is_default = TRUE LIMIT 1")
        if row: return dict(row)
        
        # Fallback if DB empty (bootstrapping)
        return {
            "name": "Sarah",
            "system_prompt": "You are Sarah, the KonexPro AI Specialist...",
            "tools": ["generate_payment_link", "update_profile"],
            "model": "gemini-2.0-flash"
        }
    except Exception:
        # DB Table might not exist yet
        return None
    finally:
        await conn.close()

# --- Payments Repository ---
async def record_payment(code: str, amount: float, currency: str, sender: str, raw_message: str):
    conn = await get_db_connection()
    try:
        await conn.execute("""
            INSERT INTO payments (code, amount, currency, sender_phone, raw_message, status)
            VALUES ($1, $2, $3, $4, $5, 'PENDING')
            ON CONFLICT (code) DO NOTHING
        """, code, amount, currency, sender, raw_message)
        return True
    except Exception as e:
        # print(f"DB Error record_payment: {e}") # Use logger in real app
        return False
    finally:
        await conn.close()

async def claim_payment(code: str, user_id: str):
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("SELECT status, amount, currency, claimed_by FROM payments WHERE code = $1", code)
        
        if not row:
            return False, "Payment code not found.", 0.0
            
        if row['status'] == 'CLAIMED':
            if row['claimed_by'] == user_id:
                return False, "You have already used this code.", 0.0
            return False, "This code has already been used by someone else.", 0.0
            
        # Atomic Update
        result = await conn.execute("""
            UPDATE payments 
            SET status = 'CLAIMED', claimed_by = $2, updated_at = NOW()
            WHERE code = $1 AND status = 'PENDING'
        """, code, user_id)
        
        if result == "UPDATE 1":
            return True, "Payment verified successfully!", float(row['amount'])
        else:
            return False, "Could not claim payment (technical conflict).", 0.0
            
    finally:
        await conn.close()
async def save_token(phone_number: str, token_info: dict):
    """
    Saves or updates the Google OAuth token for a user.
    """
    conn = await get_db_connection()
    try:
        # We store the entire JSON blob of token info
        # But we also extract the access_token for the primary column if needed
        # Assuming schema has: phone_number, access_token, refresh_token, etc.?
        # Or just a JSONB column?
        # Looking at schema.py earlier, it was:
        # access_token TEXT NOT NULL, refresh_token TEXT, token_uri TEXT, ...
        
        await conn.execute("""
            INSERT INTO ai_tokens (phone_number, access_token, refresh_token, token_uri, client_id, client_secret, scopes, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            ON CONFLICT (phone_number) DO UPDATE SET
                access_token = $2,
                refresh_token = $3,
                token_uri = $4,
                created_at = NOW();
        """, 
        phone_number, 
        token_info.get("token"),
        token_info.get("refresh_token"),
        token_info.get("token_uri"),
        token_info.get("client_id"),
        token_info.get("client_secret"),
        json.dumps(token_info.get("scopes", []))
        )
    finally:
        await conn.close()
