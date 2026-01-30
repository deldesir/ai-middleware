from app.database.connection import get_db_connection

async def init_db():
    conn = await get_db_connection()
    try:
        # 0. Enable Vector Extension (Future Proofing)
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # 1. AI Tokens (OAuth)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_tokens (
                phone_number TEXT PRIMARY KEY,
                access_token TEXT,
                refresh_token TEXT,
                client_id TEXT,
                client_secret TEXT,
                token_uri TEXT,
                scopes TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)

        # 2. Chat History
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                user_id TEXT,
                role TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_sessions(user_id);")

        # 3. User Profiles (Semantic Memory)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                user_id TEXT PRIMARY KEY,
                profile_data JSONB DEFAULT '{}'::jsonb,
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)

        # 4. Payments
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                code TEXT PRIMARY KEY,
                amount DECIMAL,
                currency TEXT,
                sender_phone TEXT,
                status TEXT DEFAULT 'PENDING',
                claimed_by TEXT,
                raw_message TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)

        # 5. Personas (New)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS personas (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                system_prompt TEXT NOT NULL,
                allowed_tools JSONB DEFAULT '[]'::jsonb,
                model_config JSONB DEFAULT '{}'::jsonb,
                owner_phone TEXT,
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Seed Default Persona if needed?
        # That's usually done in a seed script, but we can do it here for MVP convenience
        # or leave it to the application logic to handle "No Persona Found".

    finally:
        await conn.close()
