import random
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from db import *
from cases import *
from api import *
from utils import send_queue, payments
from utils import take_screenshot_and_process
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

router = Router()

class CaseEditState(StatesGroup):
    waiting_for_case_info = State()

class GiftEditState(StatesGroup):
    waiting_for_gift_info = State()
    waiting_for_gift_url = State()


# --- КОМАНДЫ ---

@router.message(F.text == "/start")
async def handle_start(message: Message):
    user_id = message.from_user.id
    
    await create_user(user_id)
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(
                text="Open Web App",
                web_app=types.WebAppInfo(url=f'https://{os.getenv("DOMAIN")}:8080/')
            )]
        ],
        resize_keyboard=True
    )

    await message.answer("🎁 Приветсвуем тебя в нашей игре!", reply_markup=keyboard)

@router.message(F.text == "/paysupport")
async def paysupport(message: types.Message):
    await message.answer("Вопросы по оплате Telegram Stars — @support_username")


@router.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    await message.answer('Введите число звезд, которое хотите заплатить')
    

@router.message(lambda m: m.text is not None and m.text.isdigit())
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
    await message.bot.send_invoice(
        chat_id=message.chat.id,
        title=f"Платёж на {amount} звёзд",
        description=f"Покупка монет на сумму {amount} звёзд",
        payload=payment_id,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="XTR", amount=amount)],
    )

@router.pre_checkout_query()
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    payment_id = pre_checkout_q.invoice_payload
    payment = payments.get(payment_id)
    if not payment or payment["paid"] or payment["amount"] != pre_checkout_q.total_amount:
        await pre_checkout_q.bot.answer_pre_checkout_query(pre_checkout_q.id, ok=False, error_message="Ошибка платежа")
        return
    await pre_checkout_q.bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

@router.message(F.successful_payment)
async def successful_payment(message: types.Message):
    payment_info = message.successful_payment
    payment_id = payment_info.invoice_payload
    payment = payments.get(payment_id)
    if payment and not payment["paid"]:
        payment["paid"] = True
        await set_user_balance(message.from_user.id, payment["amount"])
        await message.answer(
            f"Платёж {payment['amount']} звёзд принят. Зачислено {payment['amount']} монет."
        )
        new_balance = await get_user_balance(message.from_user.id)
        await message.answer(f"Ваш баланс: {new_balance} монет.")

@router.message(F.text == "/get_money")
async def handle_get_money(message: Message):
    user_id = message.from_user.id
    await set_user_balance(user_id, 1000000)
    new_balance = await get_user_balance(user_id)
    await message.answer(f"Баланс пополнен. Текущий баланс: {new_balance}₽")


# --- Админ-панель кейсов ---
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
        lines = message.text.split('\n')
        if len(lines) < 3:
            await message.answer("❌ Неверный формат. Нужно: Название\\nЦена\\nКатегория")
            return
        name = lines[0].strip()
        price = int(lines[1].strip())
        category = lines[2].strip()
        cases = load_cases()
        case = next((c for c in cases if c["id"] == case_id), None)
        if case:
            case['name'] = name
            case['price'] = price
            case['category'] = category
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
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"case_confirm_delete_{case_id}")],
        [InlineKeyboardButton(text="❌ Нет, отмена", callback_data=f"case_edit_{case_id}")]
    ])
    await callback.message.edit_text("❓ Вы уверены, что хотите удалить этот кейс?", reply_markup=keyboard)

@router.callback_query(F.data.startswith("case_confirm_delete_"))
async def handle_case_confirm_delete(callback: CallbackQuery):
    case_id = callback.data.split("_")[3]
    cases = load_cases()
    cases = [c for c in cases if c["id"] != case_id]
    save_cases(cases)
    await callback.answer("✅ Кейс удален")
    await handle_case_list(callback)

@router.callback_query(F.data == "case_create")
async def handle_case_create(callback: CallbackQuery):
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

# --- Гифты ---

@router.callback_query(F.data.startswith("gift_add_"))
async def handle_gift_add(callback: CallbackQuery):
    case_id = callback.data.split("_")[2]
    cases = load_cases()
    case = next((c for c in cases if c["id"] == case_id), None)
    if not case:
        await callback.answer("❌ Кейс не найден")
        return
    new_gift = {
        "id": f"gift-{len(case['gifts']) + 1}-{random.randint(1000, 9999)}",
        "name": "Новый подарок",
        "link": "https://example.com/gift",
        "img": "/media/gift.png",
        "chance": 0.1,
        "fake_chance": 0.1,
        "price": 100
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
        f"<code>Название\nШанс (0.0-1.0)\nФейковый шанс (0.0-1.0)\nЦена (число)</code>\n\n"
        f"Текущие данные:\n"
        f"Название: {gift['name']}\n"
        f"Шанс: {gift['chance']}\n"
        f"Фейковый шанс: {gift.get('fake_chance', 'Не указан')}\n"
        f"Цена: {gift.get('price', 'Не указана')}\n"
        f"Ссылка: {gift.get('link', 'Не указана')}\n\n"
        f"После этого отправьте новую ссылку для скриншота (если нужно)"
    )


@router.message(GiftEditState.waiting_for_gift_info)
async def handle_gift_info_input(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        case_id = data['case_id']
        gift_id = data['gift_id']
        lines = message.text.split('\n')

        if len(lines) < 4:
            await message.answer("❌ Неверный формат. Нужно: Название\nШанс\nФейковый шанс\nЦена")
            return

        name = lines[0].strip()

        # основной шанс
        chance = float(lines[1].strip())
        if not 0 <= chance <= 1:
            await message.answer("❌ Шанс должен быть между 0 и 1")
            return

        # фейковый шанс
        fake_chance = float(lines[2].strip())
        if not 0 <= fake_chance <= 1:
            await message.answer("❌ Фейковый шанс должен быть между 0 и 1")
            return

        # цена
        try:
            price = int(lines[3].strip())
            if price < 0:
                await message.answer("❌ Цена не может быть отрицательной")
                return
        except ValueError:
            await message.answer("❌ Цена должна быть целым числом")
            return

        await state.update_data(
            gift_name=name,
            gift_chance=chance,
            gift_fake_chance=fake_chance,
            gift_price=price
        )
        await state.set_state(GiftEditState.waiting_for_gift_url)

        await message.answer(
            "✅ Данные приняты!\n"
            f"Название: {name}\n"
            f"Шанс: {chance}\n"
            f"Фейковый шанс: {fake_chance}\n"
            f"Цена: {price}\n\n"
            "Теперь отправьте новую ссылку для подарка "
            "(или отправьте 'пропустить', чтобы оставить текущую)"
        )
    except ValueError:
        await message.answer("❌ Шанс, фейковый шанс и цена должны быть числами (например: 0.3, 0.7 и 150)")
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
                    asyncio.create_task(create_gift_icon_with_notification(message.bot, gift, case, message.chat.id))
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

async def create_gift_icon_with_notification(bot: Bot, gift, case, chat_id):
    try:
        await create_gift_icon(gift, take_screenshot_and_process)
        await update_case_icon(case)
        cases = load_cases()
        current_case = next((c for c in cases if c["id"] == case["id"]), None)
        if current_case:
            current_case['gifts'] = [g if g['id'] != gift['id'] else gift for g in current_case['gifts']]
            save_cases(cases)
        await bot.send_message(chat_id, f"✅ Иконка для подарка '{gift['name']}' создана успешно!")
    except Exception as e:
        error_msg = f"❌ Ошибка при создании иконки: {e}"
        print(error_msg)
        await bot.send_message(chat_id, error_msg)


# --- Кнопка "Готово" у уведомления админа ---
@router.callback_query(F.data.startswith("done_"))
async def handle_done_button(callback: types.CallbackQuery):
    try:
        data_parts = callback.data.split('_')
        if len(data_parts) >= 3:
            user_id = int(data_parts[1])
            gift_id = data_parts[2]
            await callback.message.delete()
            await callback.answer("✅ Уведомление удалено", show_alert=False)
    except Exception as e:
        print(f"Ошибка обработки кнопки 'Готово': {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=False)
