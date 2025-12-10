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
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            logo TEXT,
            published BOOLEAN DEFAULT FALSE
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS gifts (
            id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            link TEXT,
            img TEXT,
            chance REAL NOT NULL,
            fake_chance REAL NOT NULL,
            price INTEGER NOT NULL
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

# ===== CASES CRUD =====
async def create_case(case_id, category, name, price, logo=None, published=False):
    """Create a new case in the database"""
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute(
        "INSERT INTO cases (id, category, name, price, logo, published) VALUES ($1, $2, $3, $4, $5, $6)",
        case_id, category, name, price, logo, published
    )
    await conn.close()

async def get_case(case_id):
    """Get a case by ID"""
    conn = await asyncpg.connect(**DB_CONFIG)
    row = await conn.fetchrow("SELECT * FROM cases WHERE id = $1", case_id)
    await conn.close()
    return dict(row) if row else None

async def get_all_cases(published_only=False):
    """Get all cases, optionally filter by published status"""
    conn = await asyncpg.connect(**DB_CONFIG)
    if published_only:
        rows = await conn.fetch("SELECT * FROM cases WHERE published = TRUE")
    else:
        rows = await conn.fetch("SELECT * FROM cases")
    await conn.close()
    return [dict(row) for row in rows]

async def update_case(case_id, **kwargs):
    """Update a case with the provided fields"""
    conn = await asyncpg.connect(**DB_CONFIG)
    fields = []
    values = []
    for key, value in kwargs.items():
        if key in ['category', 'name', 'price', 'logo', 'published']:
            fields.append(f"{key} = ${len(values) + 1}")
            values.append(value)
    if fields:
        query = f"UPDATE cases SET {', '.join(fields)} WHERE id = ${len(values) + 1}"
        values.append(case_id)
        await conn.execute(query, *values)
    await conn.close()

async def delete_case(case_id):
    """Delete a case (gifts are deleted automatically due to CASCADE)"""
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute("DELETE FROM cases WHERE id = $1", case_id)
    await conn.close()

# ===== GIFTS CRUD =====
async def create_gift(gift_id, case_id, name, link, img, chance, fake_chance, price):
    """Create a new gift in the database"""
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute(
        "INSERT INTO gifts (id, case_id, name, link, img, chance, fake_chance, price) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
        gift_id, case_id, name, link, img, chance, fake_chance, price
    )
    await conn.close()

async def get_gift(gift_id):
    """Get a gift by ID"""
    conn = await asyncpg.connect(**DB_CONFIG)
    row = await conn.fetchrow("SELECT * FROM gifts WHERE id = $1", gift_id)
    await conn.close()
    return dict(row) if row else None

async def get_gifts_by_case(case_id):
    """Get all gifts for a specific case"""
    conn = await asyncpg.connect(**DB_CONFIG)
    rows = await conn.fetch("SELECT * FROM gifts WHERE case_id = $1", case_id)
    await conn.close()
    return [dict(row) for row in rows]

async def get_all_gifts():
    """Get all gifts from all cases"""
    conn = await asyncpg.connect(**DB_CONFIG)
    rows = await conn.fetch("SELECT * FROM gifts")
    await conn.close()
    return [dict(row) for row in rows]

async def update_gift(gift_id, **kwargs):
    """Update a gift with the provided fields"""
    conn = await asyncpg.connect(**DB_CONFIG)
    fields = []
    values = []
    for key, value in kwargs.items():
        if key in ['case_id', 'name', 'link', 'img', 'chance', 'fake_chance', 'price']:
            fields.append(f"{key} = ${len(values) + 1}")
            values.append(value)
    if fields:
        query = f"UPDATE gifts SET {', '.join(fields)} WHERE id = ${len(values) + 1}"
        values.append(gift_id)
        await conn.execute(query, *values)
    await conn.close()

async def delete_gift(gift_id):
    """Delete a gift"""
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute("DELETE FROM gifts WHERE id = $1", gift_id)
    await conn.close()

async def get_case_with_gifts(case_id):
    """Get a case with all its gifts in a single query"""
    conn = await asyncpg.connect(**DB_CONFIG)
    case_row = await conn.fetchrow("SELECT * FROM cases WHERE id = $1", case_id)
    if not case_row:
        await conn.close()
        return None
    gifts_rows = await conn.fetch("SELECT * FROM gifts WHERE case_id = $1", case_id)
    await conn.close()

    case = dict(case_row)
    case['gifts'] = [dict(row) for row in gifts_rows]
    return case

async def get_all_cases_with_gifts(published_only=False):
    """Get all cases with their gifts"""
    conn = await asyncpg.connect(**DB_CONFIG)
    if published_only:
        cases_rows = await conn.fetch("SELECT * FROM cases WHERE published = TRUE")
    else:
        cases_rows = await conn.fetch("SELECT * FROM cases")

    cases = []
    for case_row in cases_rows:
        case = dict(case_row)
        gifts_rows = await conn.fetch("SELECT * FROM gifts WHERE case_id = $1", case['id'])
        case['gifts'] = [dict(row) for row in gifts_rows]
        cases.append(case)

    await conn.close()
    return cases