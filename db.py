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
            gifts JSONB DEFAULT '[]'::jsonb,
            subscribed BOOLEAN DEFAULT FALSE,
            today_opened_cases INTEGER DEFAULT 0,
            last_visit INTEGER DEFAULT 0,
            everyday_visits INTEGER DEFAULT 0
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

async def update_user_tasks(user_id, subscribed=None, today_opened_cases=None, last_visit=None, everyday_visits=None):
    conn = await asyncpg.connect(**DB_CONFIG)
    fields = []
    values = []
    if subscribed is not None:
        fields.append("subscribed = ${}".format(len(values) + 1))
        values.append(bool(subscribed))
    if today_opened_cases is not None:
        fields.append("today_opened_cases = ${}".format(len(values) + 1))
        values.append(int(today_opened_cases))
    if last_visit is not None:
        fields.append("last_visit = ${}".format(len(values) + 1))
        values.append(int(last_visit))
    if everyday_visits is not None:
        fields.append("everyday_visits = ${}".format(len(values) + 1))
        values.append(int(everyday_visits))
    if fields:
        query = f"UPDATE users SET {', '.join(fields)} WHERE user_id = ${len(values) + 1}"
        values.append(user_id)
        await conn.execute(query, *values)
    await conn.close()

async def get_user_tasks(user_id):
    conn = await asyncpg.connect(**DB_CONFIG)
    row = await conn.fetchrow(
        "SELECT subscribed, today_opened_cases, last_visit, everyday_visits FROM users WHERE user_id = $1", user_id
    )
    await conn.close()
    if not row:
        return {"error": "Пользователь не найден"}
    return {
        "subscribed": row["subscribed"],
        "today_opened_cases": row["today_opened_cases"],
        "last_visit": row["last_visit"],
        "everyday_visits": row["everyday_visits"]
    }

async def get_profile_data_and_tasks(user_id):
    conn = await asyncpg.connect(**DB_CONFIG)
    row = await conn.fetchrow(
        "SELECT balance, gifts, subscribed, today_opened_cases, last_visit, everyday_visits FROM users WHERE user_id = $1", user_id
    )
    await conn.close()
    if not row:
        return {"error": "Пользователь не найден"}
    return {
        "balance": row["balance"],
        "gifts_json": row["gifts"],
        "subscribed": row["subscribed"],
        "today_opened_cases": row["today_opened_cases"],
        "last_visit": row["last_visit"],
        "everyday_visits": row["everyday_visits"]
    }

async def update_user_balance(user_id, amount):
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", amount, user_id)
    await conn.close()