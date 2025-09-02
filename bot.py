import asyncio
import json
import random
import ast
import aiosqlite
import os
from aiogram.filters import Command
import os
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import LabeledPrice
import requests

# Добавьте в начало файла
try:
    from screenshot_module import take_screenshot_and_process
except ImportError:
    # Заглушка для тестирования
    def take_screenshot_and_process(url, output_path, crop_x, crop_y, crop_size):
        print(f"⚠️  Скриншот не сделан (функция не импортирована): {url}")
        # Создаем пустой файл для теста
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='red')
        img.save(output_path)

API_TOKEN = "8008525871:AAFpPTPQbsF661zdGXSNRsriquhiqn-VpKQ"
ADMIN_ID = 849307631
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

send_queue = asyncio.Queue()

class CaseEditState(StatesGroup):
    waiting_for_case_info = State()

class GiftEditState(StatesGroup):
    waiting_for_gift_info = State()
    waiting_for_gift_url = State()

# --- СИНХРОННАЯ ХЕРНЯ ДЛЯ JS ---

def get_user_balance_sync(user_id):
    return asyncio.run(get_user_balance(user_id))


def try_open_case_sync(user_id, case_id):
    return asyncio.run(try_open_case(user_id, case_id))


def get_user_profile_data_sync(user_id):
    # Синхронная обёртка для асинхронной функции
    return asyncio.run(get_user_profile_data(user_id))


# --- ДЛЯ РАБОТЫ С БД ---

async def init_db():
    async with aiosqlite.connect("users.db") as db:
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


def load_cases():
    if os.path.exists("data/cases.json"):
        with open("data/cases.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_cases(cases):
    os.makedirs("data", exist_ok=True)
    with open("data/cases.json", "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)

# --- КОМАНДЫ ---

@router.message(F.text == "/start")
async def handle_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    
    async with aiosqlite.connect("users.db") as db:
        # Сначала проверяем, существует ли столбец avatar
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = await cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # Если столбца avatar нет - добавляем его
        if 'avatar' not in column_names:
            await db.execute("ALTER TABLE users ADD COLUMN avatar TEXT")
            await db.commit()
        
        # Проверяем, существует ли пользователь
        cursor = await db.execute("SELECT avatar FROM users WHERE user_id = ?", (user_id,))
        user_exists = await cursor.fetchone()
        
        if user_exists:
            # Пользователь уже существует, обновляем username если нужно
            await db.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
        else:
            # Новый пользователь
            await db.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        
        await db.commit()
    
    # Скачиваем и сохраняем аватарку
    avatar_path = await download_user_avatar(user_id)
    
    # Обновляем аватар в БД
    async with aiosqlite.connect("users.db") as db:
        await db.execute("UPDATE users SET avatar = ? WHERE user_id = ?", (avatar_path, user_id))
        await db.commit()
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(
                text="Open Web App",
                web_app=types.WebAppInfo(url='https://giftsapp.ddns.net/')
            )]
        ],
        resize_keyboard=True
    )

    await message.answer("Добро пожаловать! Ваши монеты: 0. Для пополнения отправьте число (сколько звёзд хотите обменять на монеты, 1 к 1).", reply_markup=keyboard)

@dp.message(F.text == "/paysupport")
async def paysupport(message: types.Message):
    await message.answer("Вопросы по оплате Telegram Stars — @support_username")
    
@dp.message(lambda m: m.text is not None and m.text.isdigit())
async def create_invoice(message: types.Message):
    amount = int(message.text)
    if amount <= 0:
        await message.answer("Сумма должна быть больше нуля.")
        return
    payment_id = f"{message.from_user.id}_{message.message_id}"
    payments[payment_id] = {
        "user_id": message.from_user.id,
        "amount": amount,
        "paid": False
    }
    await bot.send_invoice(
        chat_id=message.chat.id,
        title=f"Платёж на {amount} звёзд",
        description=f"Покупка монет на сумму {amount} звёзд",
        payload=payment_id,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="XTR", amount=amount)],
    )

payments = {}

@dp.pre_checkout_query()
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    payment_id = pre_checkout_q.invoice_payload
    payment = payments.get(payment_id)
    if not payment or payment["paid"] or payment["amount"] != pre_checkout_q.total_amount:
        await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=False, error_message="Ошибка платежа")
        return
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

@dp.message(F.successful_payment)
async def successful_payment(message: types.Message):
    payment_info = message.successful_payment
    payment_id = payment_info.invoice_payload
    payment = payments.get(payment_id)
    if payment and not payment["paid"]:
        payment["paid"] = True
        await add_coins(message.from_user.id, payment["amount"])
        await message.answer(
            f"Платёж {payment['amount']} звёзд принят. Зачислено {payment['amount']} монет."
        )
        await balance(message)

@router.message(F.text == "/get_money")
async def handle_get_money(message: Message):
    user_id = message.from_user.id
    await set_user_balance(user_id, 1000000)
    new_balance = await get_user_balance(user_id)
    await message.answer(f"Баланс пополнен. Текущий баланс: {new_balance}₽")

@router.message(Command("admin"))
async def handle_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Доступ запрещен")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Управление кейсами", callback_data="admin_cases")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="admin_close")]
    ])
    
    await message.answer("👑 Панель администратора", reply_markup=keyboard)

# --- ЛОГИКА ---

@router.callback_query(F.data == "admin_close")
async def handle_admin_close(callback: CallbackQuery):
    await callback.message.delete()

@router.callback_query(F.data == "admin_cases")
async def handle_admin_cases(callback: CallbackQuery):
    cases = load_cases()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать кейс", callback_data="case_create")],
        [InlineKeyboardButton(text="📋 Список кейсов", callback_data="case_list")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(f"📦 Управление кейсами\nВсего кейсов: {len(cases)}", reply_markup=keyboard)

@router.callback_query(F.data == "admin_back")
async def handle_admin_back(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Управление кейсами", callback_data="admin_cases")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="admin_close")]
    ])
    
    await callback.message.edit_text("👑 Панель администратора", reply_markup=keyboard)
    
@router.callback_query(F.data == "case_list")
async def handle_case_list(callback: CallbackQuery):
    cases = load_cases()
    
    if not cases:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Создать кейс", callback_data="case_create")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_cases")]
        ])
        await callback.message.edit_text("📦 Нет созданных кейсов", reply_markup=keyboard)
        return
    
    buttons = []
    for case in cases:
        buttons.append([InlineKeyboardButton(
            text=f"{case['name']} ({len(case['gifts'])} подарков)",
            callback_data=f"case_edit_{case['id']}"
        )])
    
    buttons.append([InlineKeyboardButton(text="➕ Создать кейс", callback_data="case_create")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_cases")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("📦 Выберите кейс для редактирования:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("case_edit_"))
async def handle_case_edit(callback: CallbackQuery):
    case_id = callback.data.split("_")[2]
    cases = load_cases()
    case = next((c for c in cases if c["id"] == case_id), None)
    
    if not case:
        await callback.answer("❌ Кейс не найден")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать информацию", callback_data=f"case_info_{case_id}")],
        [InlineKeyboardButton(text="🎁 Управление подарками", callback_data=f"case_gifts_{case_id}")],
        [InlineKeyboardButton(text="🗑️ Удалить кейс", callback_data=f"case_delete_{case_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="case_list")]
    ])
    
    await callback.message.edit_text(
        f"📦 Кейс: {case['name']}\n"
        f"💰 Цена: {case['price']}₽\n"
        f"🎁 Подарков: {len(case['gifts'])}\n"
        f"📂 Категория: {case.get('category', 'Не указана')}",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("case_info_"))
async def handle_case_info(callback: CallbackQuery, state: FSMContext):
    case_id = callback.data.split("_")[2]
    cases = load_cases()
    case = next((c for c in cases if c["id"] == case_id), None)
    
    if not case:
        await callback.answer("❌ Кейс не найден")
        return
    
    await state.set_state(CaseEditState.waiting_for_case_info)
    await state.update_data(case_id=case_id)
    
    await callback.message.edit_text(
        f"📝 Редактирование кейса: {case['name']}\n\n"
        f"Отправьте данные в формате:\n"
        f"<code>Название\nЦена\nКатегория</code>\n\n"
        f"Текущие данные:\n"
        f"Название: {case['name']}\n"
        f"Цена: {case['price']}\n"
        f"Категория: {case.get('category', 'Не указана')}"
    )

@router.message(CaseEditState.waiting_for_case_info)
async def handle_case_info_input(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        case_id = data['case_id']
        
        # Парсим введенные данные
        lines = message.text.split('\n')
        if len(lines) < 3:
            await message.answer("❌ Неверный формат. Нужно: Название\\nЦена\\nКатегория")
            return
        
        name = lines[0].strip()
        price = int(lines[1].strip())
        category = lines[2].strip()
        
        # Обновляем кейс
        cases = load_cases()
        case = next((c for c in cases if c["id"] == case_id), None)
        
        if case:
            case['name'] = name
            case['price'] = price
            case['category'] = category
            
            # Обновляем иконку кейса (самый редкий подарок)
            await update_case_icon(case)
            
            save_cases(cases)
            
            await message.answer("✅ Данные кейса обновлены!")
        else:
            await message.answer("❌ Кейс не найден")
            
    except ValueError:
        await message.answer("❌ Цена должна быть числом")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    
    await state.clear()
    
async def update_case_icon(case):
    if not case['gifts']:
        return
    
    # Находим самый редкий подарок
    rarest_gift = min(case['gifts'], key=lambda x: x['chance'])
    
    # Используем уже существующую иконку подарка
    if rarest_gift.get('img'):
        case['logo'] = rarest_gift['img']
        print(f"✅ Иконка кейса {case['id']} обновлена: {rarest_gift['img']}")

@router.callback_query(F.data.startswith("case_gifts_"))
async def handle_case_gifts(callback: CallbackQuery):
    case_id = callback.data.split("_")[2]
    cases = load_cases()
    case = next((c for c in cases if c["id"] == case_id), None)
    
    if not case:
        await callback.answer("❌ Кейс не найден")
        return
    
    buttons = []
    for gift in case["gifts"]:
        buttons.append([InlineKeyboardButton(
            text=f"{gift['name']} ({gift['chance']*100}%)",
            callback_data=f"gift_edit_{case_id}_{gift['id']}"
        )])
    
    buttons.append([InlineKeyboardButton(text="➕ Добавить подарок", callback_data=f"gift_add_{case_id}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"case_edit_{case_id}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(f"🎁 Подарки в кейсе {case['name']}:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("case_delete_"))
async def handle_case_delete(callback: CallbackQuery):
    case_id = callback.data.split("_")[2]
    cases = load_cases()
    
    # Подтверждение удаления
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"case_confirm_delete_{case_id}")],
        [InlineKeyboardButton(text="❌ Нет, отмена", callback_data=f"case_edit_{case_id}")]
    ])
    
    await callback.message.edit_text("❓ Вы уверены, что хотите удалить этот кейс?", reply_markup=keyboard)

@router.callback_query(F.data.startswith("case_confirm_delete_"))
async def handle_case_confirm_delete(callback: CallbackQuery):
    case_id = callback.data.split("_")[3]
    cases = load_cases()
    
    # Удаляем кейс
    cases = [c for c in cases if c["id"] != case_id]
    save_cases(cases)
    
    await callback.answer("✅ Кейс удален")
    await handle_case_list(callback)

@router.callback_query(F.data == "case_create")
async def handle_case_create(callback: CallbackQuery):
    # Создаем новый кейс с базовыми параметрами
    cases = load_cases()
    
    new_case = {
        "id": f"case-{len(cases) + 1}",
        "category": "basic",
        "name": f"Новый кейс {len(cases) + 1}",
        "price": 100,
        "logo": "/media/default.png",
        "gifts": []
    }
    
    cases.append(new_case)
    save_cases(cases)
    
    await callback.answer("✅ Новый кейс создан")
    await handle_case_edit(callback)
    
@router.callback_query(F.data.startswith("gift_add_"))
async def handle_gift_add(callback: CallbackQuery):
    case_id = callback.data.split("_")[2]
    cases = load_cases()
    case = next((c for c in cases if c["id"] == case_id), None)
    
    if not case:
        await callback.answer("❌ Кейс не найден")
        return
    
    # Создаем новый подарок
    new_gift = {
        "id": f"gift-{len(case['gifts']) + 1}-{random.randint(1000, 9999)}",  # Добавляем случайность чтобы избежать конфликтов
        "name": "Новый подарок",
        "link": "https://example.com/gift",
        "img": "/media/gift.png",
        "chance": 0.1
    }
    
    case["gifts"].append(new_gift)
    save_cases(cases)
    
    await callback.answer("✅ Подарок добавлен")
    await handle_case_gifts(callback)

@router.callback_query(F.data.startswith("gift_edit_"))
async def handle_gift_edit(callback: CallbackQuery, state: FSMContext):
    data_parts = callback.data.split("_")
    case_id = data_parts[2]
    gift_id = data_parts[3]
    
    cases = load_cases()
    case = next((c for c in cases if c["id"] == case_id), None)
    
    if not case:
        await callback.answer("❌ Кейс не найден")
        return
    
    gift = next((g for g in case["gifts"] if g["id"] == gift_id), None)
    
    if not gift:
        await callback.answer("❌ Подарок не найден")
        return
    
    await state.set_state(GiftEditState.waiting_for_gift_info)
    await state.update_data(case_id=case_id, gift_id=gift_id)
    
    await callback.message.edit_text(
        f"🎁 Редактирование подарка: {gift['name']}\n\n"
        f"Отправьте данные в формате:\n"
        f"<code>Название\nШанс (0.0-1.0)</code>\n\n"
        f"Текущие данные:\n"
        f"Название: {gift['name']}\n"
        f"Шанс: {gift['chance']}\n"
        f"Ссылка: {gift.get('link', 'Не указана')}\n\n"
        f"После этого отправьте новую ссылку для скриншота (если нужно)"
    )

@router.message(GiftEditState.waiting_for_gift_info)
async def handle_gift_info_input(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        case_id = data['case_id']
        gift_id = data['gift_id']
        
        # Парсим введенные данные
        lines = message.text.split('\n')
        if len(lines) < 2:
            await message.answer("❌ Неверный формат. Нужно: Название\\nШанс")
            return
        
        name = lines[0].strip()
        chance = float(lines[1].strip())
        
        if not 0 <= chance <= 1:
            await message.answer("❌ Шанс должен быть между 0 и 1")
            return
        
        # Обновляем данные в состоянии
        await state.update_data(gift_name=name, gift_chance=chance)
        await state.set_state(GiftEditState.waiting_for_gift_url)
        
        await message.answer(
            "✅ Данные приняты! Теперь отправьте новую ссылку для подарка "
            "(или отправьте 'пропустить' чтобы оставить текущую)"
        )
            
    except ValueError:
        await message.answer("❌ Шанс должен быть числом (например: 0.3)")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        await state.clear()

@router.message(GiftEditState.waiting_for_gift_url)
async def handle_gift_url_input(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        case_id = data['case_id']
        gift_id = data['gift_id']
        name = data['gift_name']
        chance = data['gift_chance']
        
        new_url = message.text.strip() if message.text.strip().lower() != 'пропустить' else None
        
        # Обновляем подарок
        cases = load_cases()
        case = next((c for c in cases if c["id"] == case_id), None)
        
        if case:
            gift = next((g for g in case["gifts"] if g["id"] == gift_id), None)
            
            if gift:
                gift['name'] = name
                gift['chance'] = chance
                
                if new_url:
                    gift['link'] = new_url
                    # Создаем новую иконку для подарка
                    await create_gift_icon(gift)
                
                save_cases(cases)
                
                # Обновляем иконку кейса
                await update_case_icon(case)
                save_cases(cases)
                
                await message.answer("✅ Подарок обновлен!")
            else:
                await message.answer("❌ Подарок не найден")
        else:
            await message.answer("❌ Кейс не найден")
            
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    
    await state.clear()

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
        # читаем список
        gifts_list = json.loads(gifts_raw) if gifts_raw else []
        gifts_list.append(selected_gift["id"])
        
        # сохраняем обратно
        await db.execute(
            "UPDATE users SET balance = ?, gifts = ? WHERE user_id = ?",
            (new_balance, json.dumps(gifts_list), user_id)
        )


        send_win_notification_to_admin_sync(user_id, selected_gift, case_id)


        # Отдаём подарок
        return {
            "gift": {
                "id": selected_gift["id"],
                "name": selected_gift.get("name", ""),
                "img": selected_gift.get("img", ""),
                "link": selected_gift.get("link", "")
            }
        }

async def create_gift_icon(gift):
    if gift.get('link'):
        try:
            # Создаем папку для иконок подарков
            os.makedirs("media/gifts", exist_ok=True)
            output_path = f"media/gifts/{gift['id']}.png"
            
            # Запускаем синхронную функцию в отдельном потоке
            await asyncio.to_thread(
                take_screenshot_and_process,
                gift['link'], 
                output_path,
                crop_x=527,
                crop_y=120,
                crop_size=255
            )
            
            gift['img'] = f"/{output_path}"
            print(f"✅ Иконка подарка {gift['id']} создана: {output_path}")
            
        except Exception as e:
            print(f"❌ Ошибка при создании иконки подарка {gift['id']}: {e}")
            # Можно добавить заглушку или оставить текущую иконку

@router.message(GiftEditState.waiting_for_gift_url)
async def handle_gift_url_input(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        case_id = data['case_id']
        gift_id = data['gift_id']
        name = data['gift_name']
        chance = data['gift_chance']
        
        new_url = message.text.strip() if message.text.strip().lower() != 'пропустить' else None
        
        # Обновляем подарок
        cases = load_cases()
        case = next((c for c in cases if c["id"] == case_id), None)
        
        if case:
            gift = next((g for g in case["gifts"] if g["id"] == gift_id), None)
            
            if gift:
                gift['name'] = name
                gift['chance'] = chance
                
                if new_url:
                    gift['link'] = new_url
                    # Запускаем создание иконки в фоне
                    asyncio.create_task(create_gift_icon_with_notification(gift, case, message.chat.id))
                    await message.answer("⏳ Создаю иконку из ссылки... Это может занять несколько секунд")
                else:
                    await message.answer("✅ Подарок обновлен (ссылка не изменена)!")
                
                save_cases(cases)
                
            else:
                await message.answer("❌ Подарок не найден")
        else:
            await message.answer("❌ Кейс не найден")
            
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    
    await state.clear()

async def create_gift_icon_with_notification(gift, case, chat_id):
    """Создает иконку и отправляет уведомление о завершении"""
    try:
        await create_gift_icon(gift)
        
        # Обновляем иконку кейса
        await update_case_icon(case)
        
        # Сохраняем изменения
        cases = load_cases()
        current_case = next((c for c in cases if c["id"] == case["id"]), None)
        if current_case:
            current_case['gifts'] = [g if g['id'] != gift['id'] else gift for g in current_case['gifts']]
            save_cases(cases)
        
        # Отправляем уведомление
        await bot.send_message(chat_id, f"✅ Иконка для подарка '{gift['name']}' создана успешно!")
        
    except Exception as e:
        error_msg = f"❌ Ошибка при создании иконки: {e}"
        print(error_msg)
        await bot.send_message(chat_id, error_msg)

# --- ОЧЕРЕДЬ ---

async def send_plus_prompt(user_id):
    await bot.send_message(user_id, "Введите сумму пополнения (число):")


async def queue_watcher():
    while True:
        user_id = await send_queue.get()
        print("queue_watcher: отправляю сообщение", user_id)
        await send_plus_prompt(user_id)


# --- ПРОЧЕЕ ---

async def download_user_avatar(user_id):
    photos = await bot.get_user_profile_photos(user_id, limit=1)
    if photos.total_count > 0:
        file_id = photos.photos[0][0].file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        # Скачиваем файл
        destination_folder = "profile_picture"
        os.makedirs(destination_folder, exist_ok=True)
        destination_path = os.path.join(destination_folder, f"{user_id}.png")
        await bot.download_file(file_path, destination_path)
        return destination_path
    return None

async def get_user_avatar(user_id):
    photos = await bot.get_user_profile_photos(user_id, limit=1)
    if photos.total_count > 0:
        file_id = photos.photos[0][0].file_id
        file = await bot.get_file(file_id)
        return f"https://api.telegram.org/file/bot{API_TOKEN}/{file.file_path}"
    return None

async def get_user_profile_data(user_id):
    async with aiosqlite.connect("users.db") as db:
        async with db.execute(
            "SELECT username, balance, gifts, avatar FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return {"error": "Пользователь не найден"}
            username, balance, gifts_json, avatar_path = row

            gifts_ids = json.loads(gifts_json) if gifts_json else []

    # Загружаем все подарки
    with open("data/cases.json", "r", encoding="utf-8") as f:
        cases = json.load(f)

    gift_info = {gift["id"]: gift for case in cases for gift in case["gifts"]}

    user_gifts = [gift_info[gid] for gid in gifts_ids if gid in gift_info]

    avatar_file = f"/{avatar_path}" if avatar_path and os.path.isfile(avatar_path) else None

    return {
        "username": username,
        "balance": balance,
        "avatar": avatar_file,
        "gifts": user_gifts
    }


def send_win_notification_to_admin_sync(user_id, gift, case_id):
    message_text = (
        f"🎉 Кто-то выиграл приз!\n\n"
        f"👤 Пользователь: {user_id}\n"
        f"🎁 Приз: {gift['name']}\n"
        f"📦 Кейс ID: {case_id}\n\n"
        f"Отправьте подарок этому пользователю!"
    )

    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": ADMIN_ID,
        "text": message_text
    })

    print(resp.json())
        
@router.callback_query(F.data.startswith("done_"))
async def handle_done_button(callback: types.CallbackQuery):
    try:
        # Разбираем данные callback
        data_parts = callback.data.split('_')
        if len(data_parts) >= 3:
            user_id = int(data_parts[1])
            gift_id = data_parts[2]
            
            # Удаляем сообщение с уведомлением
            await callback.message.delete()
            
            # Отправляем подтверждение админу
            await callback.answer("✅ Уведомление удалено", show_alert=False)
            
    except Exception as e:
        print(f"Ошибка обработки кнопки 'Готово': {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=False)

# --- ОСНОВНОЙ ЦИКЛ ---

async def main():
    dp.include_router(router)
    await init_db()
    asyncio.create_task(queue_watcher())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
