import asyncio
import os
import sys

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_connection

async def main():
    print("Connecting to DB...")
    conn = await get_db_connection()
    try:
        # Find active users in last 30 mins (safe buffer)
        rows = await conn.fetch("SELECT DISTINCT user_id FROM chat_sessions WHERE created_at > NOW() - INTERVAL '30 minutes'")
        
        if not rows:
            print("No active users found in the last 30 minutes.")
            return

        users = [r['user_id'] for r in rows]
        print(f"Found active users: {users}")
        
        # Delete history
        await conn.execute("DELETE FROM chat_sessions WHERE user_id = ANY($1)", users)
        print(f"✅ History cleared for {len(users)} users.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
