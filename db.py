import aiosqlite
import json
import os
import asyncio

DB_PATH = "users.db"

def get_user_balance_sync(user_id):
    return asyncio.run(get_user_balance(user_id))

def get_user_profile_data_sync(user_id):
    return asyncio.run(get_user_profile_data(user_id))

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0,
                gifts TEXT DEFAULT '[]',
                avatar TEXT
            )
        """)
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance, gifts FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def update_user_balance_and_gifts(user_id, new_balance, new_gifts):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance = ?, gifts = ? WHERE user_id = ?",
                         (new_balance, json.dumps(new_gifts), user_id))
        await db.commit()

async def set_user_balance(user_id, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

async def get_user_balance(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def get_user_profile_data(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT username, balance, gifts, avatar FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return {"error": "Пользователь не найден"}
            username, balance, gifts_json, avatar_path = row

    return {
        "username": username,
        "balance": balance,
        "gifts_json": gifts_json,
        "avatar_path": avatar_path
    }

async def update_user_avatar(user_id, avatar_path):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET avatar = ? WHERE user_id = ?", (avatar_path, user_id))
        await db.commit()

async def create_or_update_user(user_id, username):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = await cursor.fetchall()
        column_names = [column[1] for column in columns]
        if 'avatar' not in column_names:
            await db.execute("ALTER TABLE users ADD COLUMN avatar TEXT")
            await db.commit()
        cursor = await db.execute("SELECT avatar FROM users WHERE user_id = ?", (user_id,))
        user_exists = await cursor.fetchone()
        if user_exists:
            await db.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
        else:
            await db.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        await db.commit()