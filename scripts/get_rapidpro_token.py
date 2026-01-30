import asyncio
import asyncpg
import os

DSN = "postgresql://temba:temba@127.0.0.1:5432/temba"

async def get_token():
    print("Connecting to DB...")
    conn = await asyncpg.connect(DSN)
    try:
        # List tables
        rows = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        print("Tables found:", [r['table_name'] for r in rows])

        # Get explicit user
        target_email = "deldesir@gmail.com"
        print(f"🔎 Searching for user {target_email}...")
        # Check permissions
        user = await conn.fetchrow("SELECT id, email, is_active, is_staff, is_superuser FROM users_user WHERE email = $1", target_email)
        
        if not user:
            print(f"❌ User {target_email} not found.")
            return

        print(f"✅ Found User: {user['email']} (ID: {user['id']})")
        print(f"   Active: {user['is_active']}, Staff: {user['is_staff']}, Superuser: {user['is_superuser']}")
        
        # Check Org Membership
        orgs = await conn.fetch("SELECT * FROM orgs_orgmembership WHERE user_id = $1", user['id'])
        print(f"   Org Memberships: {len(orgs)}")
        for o in orgs:
            # Inspect keys
            print(f"   - Keys: {list(o.keys())}")
            
            print(f"   - Org: {o['org_id']}, Role Code: {o['role_code']}")
            
            if o['role_code'] != 'A':
                print("⚠️  User is not Organization Admin. Promoting...")
                await conn.execute("UPDATE orgs_orgmembership SET role_code = 'A' WHERE id = $1", o['id'])
                print("✅  Promoted to Org Admin.")
        if not user['is_superuser']:
            print("⚠️ User is not superuser. Elevating...")
            await conn.execute("UPDATE users_user SET is_superuser = true, is_staff = true, is_active = true WHERE id = $1", user['id'])
            print("✅ User elevated to Superuser.")

        # Check Token provided by user
        PROVIDED_TOKEN = "GJ3ZQ8HZEWZQUENXBQ9R8Z9LKSLJFXUYU6EYWZUN"
        
        # Get Real Token
        token = await conn.fetchrow("SELECT key FROM authtoken_token WHERE user_id = $1", user['id'])
        if token:
             print(f"🔑 DB Token (authtoken): {token['key']}")
             if token['key'] == PROVIDED_TOKEN:
                 print("✅ Token MATCHES user input.")
             else:
                 print("⚠️ Token MISMATCH. Updating authtoken to match provided token...")
                 await conn.execute("UPDATE authtoken_token SET key = $1 WHERE user_id = $2", PROVIDED_TOKEN, user['id'])
                 print("✅ Token Updated.")
        else:
             print("❌ No authtoken found. Migrating provided token...")
             await conn.execute("INSERT INTO authtoken_token (key, created, user_id) VALUES ($1, NOW(), $2)", PROVIDED_TOKEN, user['id'])
             print("✅ Token Inserted into authtoken_token.")
             
        # Check Legacy
        legacy = await conn.fetchrow("SELECT key FROM api_apitoken WHERE user_id = $1", user['id'])
        if legacy:
             print(f"🔑 DB Token (api): {legacy['key']}")
             if legacy['key'] == PROVIDED_TOKEN:
                 print("✅ Legacy Token MATCHES user input.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(get_token())
