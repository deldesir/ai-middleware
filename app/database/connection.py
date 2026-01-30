import os
import asyncpg
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://temba:temba@127.0.0.1:5432/temba")

async def get_db_connection():
    """Returns a connection to the configured PostgreSQL database."""
    try:
        return await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"❌ DB Connection Failed: {e}")
        raise e

async def check_health():
    try:
        conn = await get_db_connection()
        await conn.execute("SELECT 1")
        await conn.close()
        return True
    except Exception:
        return False
