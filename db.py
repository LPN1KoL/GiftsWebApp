import asyncpg
import asyncio
import json

DB_CONFIG = {
    "user": "root",
    "password": "123",
    "database": "sss",
    "host": "localhost",
    "port": 5432
}

# ===== СИНХРОННЫЕ ОБЁРТКИ =====
def get_user_balance_sync(user_id):
    return asyncio.run(get_user_balance(user_id))

def get_user_profile_data_sync(user_id):
    return asyncio.run(get_user_profile_data(user_id))

# ===== ИНИЦИАЛИЗАЦИЯ БД =====
async def init_db():
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            gifts JSONB DEFAULT '[]'::jsonb
        )
    """)
    await conn.close()

# ===== CRUD =====
async def create_user(user_id):
    conn = await asyncpg.connect(**DB_CONFIG)
    user_exists = await conn.fetchrow("SELECT user_id FROM users WHERE user_id = $1", user_id)
    if not user_exists:
        await conn.execute("INSERT INTO users (user_id) VALUES ($1) ON CONFLICT DO NOTHING", user_id)
    await conn.close()


async def get_user(user_id):
    conn = await asyncpg.connect(**DB_CONFIG)
    row = await conn.fetchrow("SELECT balance, gifts FROM users WHERE user_id = $1", user_id)
    await conn.close()
    return row

async def update_user_balance_and_gifts(user_id, new_balance, new_gifts):
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute(
        "UPDATE users SET balance = $1, gifts = $2 WHERE user_id = $3",
        new_balance, json.dumps(new_gifts), user_id
    )
    await conn.close()

async def set_user_balance(user_id, amount):
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", amount, user_id)
    await conn.close()

async def get_user_balance(user_id):
    conn = await asyncpg.connect(**DB_CONFIG)
    row = await conn.fetchrow("SELECT balance FROM users WHERE user_id = $1", user_id)
    await conn.close()
    return row["balance"] if row else None

async def get_user_profile_data(user_id):
    conn = await asyncpg.connect(**DB_CONFIG)
    row = await conn.fetchrow(
        "SELECT balance, gifts FROM users WHERE user_id = $1", user_id
    )
    await conn.close()
    if not row:
        return {"error": "Пользователь не найден"}
    return {
        "balance": row["balance"],
        "gifts_json": row["gifts"]
    }


