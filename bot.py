import asyncio
import json
import random
import ast
import aiosqlite
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.types import Message

API_TOKEN = "TOKEN"
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

send_queue = asyncio.Queue()

# --- СИНХРОННАЯ ХЕРНЯ ДЛЯ JS ---

def get_user_balance_sync(user_id):
    return asyncio.run(get_user_balance(user_id))


def try_open_case_sync(user_id, case_id):
    return asyncio.run(try_open_case(user_id, case_id))



def get_user_profile_data_sync(user_id):
    return "бля, я хз эта хуйня чё-то не работает, а у меня уже мозги не варят"


# --- ДЛЯ РАБОТЫ С БД ---

async def init_db():
    async with aiosqlite.connect("users.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0,
                gifts TEXT DEFAULT '[]'
            )
        """)
        await db.commit()


async def get_user(user_id):
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("SELECT balance, gifts FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()


async def update_user_balance_and_gifts(user_id, new_balance, new_gifts):
    async with aiosqlite.connect("users.db") as db:
        await db.execute("UPDATE users SET balance = ?, gifts = ? WHERE user_id = ?",
                         (new_balance, json.dumps(new_gifts), user_id))
        await db.commit()


async def set_user_balance(user_id, amount):
    async with aiosqlite.connect("users.db") as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()


async def get_user_balance(user_id):
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


# --- КОМАНДЫ ---

@router.message(F.text == "/start")
async def handle_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    async with aiosqlite.connect("users.db") as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        await db.commit()
    await message.answer("Вы зарегистрированы.")


@router.message(F.text == "/get_money")
async def handle_get_money(message: Message):
    user_id = message.from_user.id
    await set_user_balance(user_id, 1000000)
    new_balance = await get_user_balance(user_id)
    await message.answer(f"Баланс пополнен. Текущий баланс: {new_balance}₽")


# --- ЛОГИКА ---

async def try_open_case(user_id, case_id):
    # Загрузка кейсов
    with open("data/cases.json", "r", encoding="utf-8") as f:
        cases = json.load(f)

    case = next((c for c in cases if c["id"] == case_id), None)
    if not case:
        return {"error": "Кейс не найден"}

    price = case["price"]

    # Получение баланса и подарков
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("SELECT balance, gifts FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return {"error": "Пользователь не найден"}

            balance, gifts_raw = row
            if balance < price:
                return {"error": f"Недостаточно средств: нужно {price - balance}₽"}

        # Выбор подарка
        rnd = random.random()
        cumulative = 0
        selected_gift = None
        for gift in case["gifts"]:
            cumulative += gift["chance"]
            if rnd <= cumulative:
                selected_gift = gift
                break

        if not selected_gift:
            selected_gift = case["gifts"][-1]

        # Обновление баланса и добавление подарка
        new_balance = balance - price
        gifts_list = ast.literal_eval(gifts_raw)
        gifts_list.append(selected_gift["id"])

        await db.execute(
            "UPDATE users SET balance = ?, gifts = ? WHERE user_id = ?",
            (new_balance, json.dumps(gifts_list), user_id)
        )
        await db.commit()

        # Отдаём подарок
        return {
            "gift": {
                "id": selected_gift["id"],
                "name": selected_gift.get("name", ""),
                "img": selected_gift.get("img", ""),
                "link": selected_gift.get("link", "")
            }
        }



# --- ОЧЕРЕДЬ ---

async def send_plus_prompt(user_id):
    await bot.send_message(user_id, "Введите сумму пополнения (число):")


async def queue_watcher():
    while True:
        user_id = await send_queue.get()
        print("queue_watcher: отправляю сообщение", user_id)
        await send_plus_prompt(user_id)


# --- ПРОЧЕЕ ---

async def get_user_avatar(user_id):
    photos = await bot.get_user_profile_photos(user_id, limit=1)
    if photos.total_count > 0:
        file_id = photos.photos[0][0].file_id
        file = await bot.get_file(file_id)
        return f"https://api.telegram.org/file/bot{API_TOKEN}/{file.file_path}"
    return None

async def get_user_profile_data(user_id):
    async with aiosqlite.connect("users.db") as db:
        # Получаем username, balance, gifts
        async with db.execute("SELECT username, balance, gifts FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return {"error": "Пользователь не найден"}
            username, balance, gifts_json = row
            gifts_ids = json.loads(gifts_json)

    # Загружаем все подарки из кейсов
    with open("data/cases.json", "r", encoding="utf-8") as f:
        cases = json.load(f)
    
    gift_info = {}
    for case in cases:
        for gift in case["gifts"]:
            gift_info[gift["id"]] = gift

    user_gifts = [gift_info[gid] for gid in gifts_ids if gid in gift_info]

    avatar = await get_user_avatar(user_id)

    return {
        "username": username,
        "balance": balance,
        "avatar": avatar,
        "gifts": user_gifts
    }


# --- ОСНОВНОЙ ЦИКЛ ---

async def main():
    dp.include_router(router)
    await init_db()
    asyncio.create_task(queue_watcher())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
