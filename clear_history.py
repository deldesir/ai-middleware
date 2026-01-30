import asyncio
from db import init_db, get_db_connection

async def clear_chat():
    conn = await get_db_connection()
    try:
        # Clear specific user history
        await conn.execute("DELETE FROM chat_sessions WHERE user_id = 'whatsapp:50942614949'")
        print("✅ History Cleared for whatsapp:50942614949")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(clear_chat())
