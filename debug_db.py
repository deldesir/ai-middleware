import asyncio
from db import get_token, init_db

async def check_db():
    await init_db()
    token = await get_token("1234567890")
    print(f"Token Record: {token}")

if __name__ == "__main__":
    asyncio.run(check_db())
