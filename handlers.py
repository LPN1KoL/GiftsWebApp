import random
import os
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from PIL import Image

from db import *
from cases import *
from api import *
from utils import send_queue, payments
from utils import take_screenshot_and_process
from utils import remove_background
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

router = Router()

class CaseEditState(StatesGroup):
    waiting_for_case_info = State()

class CaseCreateState(StatesGroup):
    waiting_for_case_info = State()

class GiftEditState(StatesGroup):
    waiting_for_gift_info = State()
    waiting_for_gift_url = State()

class GiftCreateState(StatesGroup):
    waiting_for_gift_info = State()
    waiting_for_gift_photo = State()


# --- КОМАНДЫ ---

@router.message(F.text == "/start")
async def handle_start(message: Message):
    user_id = message.from_user.id
    
    await create_user(user_id)
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(
                text="Open Web App",
                web_app=types.WebAppInfo(url=f'https://{os.getenv("DOMAIN")}/')
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
    await message.answer(f"Баланс пополнен. Текущий баланс: {new_balance}")


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
    cases = await load_cases()
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
    cases = await load_cases()
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
    case = await get_case_by_id(case_id)
    if not case:
        await callback.answer("❌ Кейс не найден")
        return

    # Определяем текст для кнопки (если уже опубликован — пишем, что опубликован)
    publish_btn_text = "📢 Опубликовать кейс" if not case.get("published", False) else "✅ Кейс опубликован"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать информацию", callback_data=f"case_info_{case_id}")],
        [InlineKeyboardButton(text="🎁 Управление подарками", callback_data=f"case_gifts_{case_id}")],
        [InlineKeyboardButton(text=publish_btn_text, callback_data=f"case_publish_{case_id}")],
        [InlineKeyboardButton(text="🗑️ Удалить кейс", callback_data=f"case_delete_{case_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="case_list")]
    ])

    await callback.message.edit_text(
        f"📦 Кейс: {case['name']}\n"
        f"💰 Цена: {case['price']}₽\n"
        f"🎁 Подарков: {len(case['gifts'])}\n"
        f"📂 Категория: {case.get('category', 'Не указана')}\n"
        f"📢 Статус: {'✅ Опубликован' if case.get('published', False) else '❌ Не опубликован'}",
        reply_markup=keyboard
    )





@router.callback_query(F.data.startswith("case_publish_"))
async def handle_case_publish(callback: CallbackQuery):
    from db import update_case
    case_id = callback.data.split("_")[2]
    case = await get_case_by_id(case_id)

    if not case:
        await callback.answer("❌ Кейс не найден", show_alert=True)
        return

    if case.get("published", False):
        await callback.answer("⚠️ Кейс уже опубликован", show_alert=True)
        return

    await update_case(case_id, published=True)

    await callback.answer("✅ Кейс опубликован")
    await handle_case_edit(callback)



@router.callback_query(F.data.startswith("case_info_"))
async def handle_case_info(callback: CallbackQuery, state: FSMContext):
    case_id = callback.data.split("_")[2]
    case = await get_case_by_id(case_id)
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
    from db import update_case
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
        case = await get_case_by_id(case_id)
        if case:
            await update_case(case_id, name=name, price=price, category=category)
            case['name'] = name
            case['price'] = price
            case['category'] = category
            await update_case_icon(case)
            # Update the logo in database after icon update
            await update_case(case_id, logo=case.get('logo'))
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
    case = await get_case_by_id(case_id)
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
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"case_confirm_delete_{case_id}")],
        [InlineKeyboardButton(text="❌ Нет, отмена", callback_data=f"case_edit_{case_id}")]
    ])
    await callback.message.edit_text("❓ Вы уверены, что хотите удалить этот кейс?", reply_markup=keyboard)

@router.callback_query(F.data.startswith("case_confirm_delete_"))
async def handle_case_confirm_delete(callback: CallbackQuery):
    from db import delete_case
    case_id = callback.data.split("_")[3]
    await delete_case(case_id)
    await callback.answer("✅ Кейс удален")
    await handle_case_list(callback)

@router.callback_query(F.data == "case_create")
async def handle_case_create(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CaseCreateState.waiting_for_case_info)
    await callback.message.edit_text(
        f"➕ Создание нового кейса\n\n"
        f"Отправьте данные в формате:\n"
        f"<code>Название\nЦена (число)\nКатегория</code>\n\n"
        f"Пример:\n"
        f"<code>Золотой кейс\n500\nbasic</code>"
    )

@router.message(CaseCreateState.waiting_for_case_info)
async def handle_case_create_info(message: Message, state: FSMContext):
    from db import create_case
    try:
        lines = message.text.split('\n')
        if len(lines) < 3:
            await message.answer("❌ Неверный формат. Нужно: Название\\nЦена\\nКатегория")
            return

        name = lines[0].strip()
        try:
            price = int(lines[1].strip())
            if price < 0:
                await message.answer("❌ Цена не может быть отрицательной")
                return
        except ValueError:
            await message.answer("❌ Цена должна быть целым числом")
            return

        category = lines[2].strip()

        # Find the maximum case number to avoid duplicate IDs
        cases = await load_cases()
        max_case_num = 0
        for case in cases:
            case_id = case.get('id', '')
            if case_id.startswith('case-'):
                try:
                    case_num = int(case_id.split('-')[1])
                    max_case_num = max(max_case_num, case_num)
                except (ValueError, IndexError):
                    # Skip cases with invalid ID format
                    pass

        new_case_num = max_case_num + 1
        new_case_id = f"case-{new_case_num}"

        # Create the case with user-provided data
        # Cases are created as unpublished by default and must be explicitly published
        await create_case(
            new_case_id,
            category,
            name,
            price,
            "/media/default.png",
            False  # Cases are unpublished by default
        )

        await message.answer("✅ Новый кейс создан!")

        # Show the newly created case details
        case = await get_case_by_id(new_case_id)
        if not case:
            print(f"❌ Failed to retrieve case {new_case_id} after creation")
            await message.answer("❌ Ошибка при создании кейса")
            await state.clear()
            return

        print(f"✅ Case {new_case_id} retrieved successfully and will be shown to user")

        # Определяем текст для кнопки (если уже опубликован — пишем, что опубликован)
        publish_btn_text = "📢 Опубликовать кейс" if not case.get("published", False) else "✅ Кейс опубликован"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Редактировать информацию", callback_data=f"case_info_{new_case_id}")],
            [InlineKeyboardButton(text="🎁 Управление подарками", callback_data=f"case_gifts_{new_case_id}")],
            [InlineKeyboardButton(text=publish_btn_text, callback_data=f"case_publish_{new_case_id}")],
            [InlineKeyboardButton(text="🗑️ Удалить кейс", callback_data=f"case_delete_{new_case_id}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="case_list")]
        ])

        await message.answer(
            f"📦 Кейс: {case['name']}\n"
            f"💰 Цена: {case['price']}₽\n"
            f"🎁 Подарков: {len(case['gifts'])}\n"
            f"📂 Категория: {case.get('category', 'Не указана')}\n"
            f"📢 Статус: {'✅ Опубликован' if case.get('published', False) else '❌ Не опубликован'}",
            reply_markup=keyboard
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    finally:
        await state.clear()

# --- Гифты ---

@router.callback_query(F.data.startswith("gift_add_"))
async def handle_gift_add(callback: CallbackQuery, state: FSMContext):
    case_id = callback.data.split("_")[2]
    case = await get_case_by_id(case_id)
    if not case:
        await callback.answer("❌ Кейс не найден")
        return

    await state.set_state(GiftCreateState.waiting_for_gift_info)
    await state.update_data(case_id=case_id)
    await callback.message.edit_text(
        f"➕ Создание нового подарка для кейса: {case['name']}\n\n"
        f"Отправьте данные в формате:\n"
        f"<code>Название\nШанс (0.0-1.0)\nФейковый шанс (0.0-1.0)\nЦена (число)</code>\n\n"
        f"Пример:\n"
        f"<code>iPhone 15 Pro\n0.05\n0.15\n120000</code>"
    )


@router.message(GiftCreateState.waiting_for_gift_info)
async def handle_gift_create_info(message: Message, state: FSMContext):
    try:
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
        await state.set_state(GiftCreateState.waiting_for_gift_photo)

        await message.answer(
            "✅ Данные приняты!\n"
            f"Название: {name}\n"
            f"Шанс: {chance}\n"
            f"Фейковый шанс: {fake_chance}\n"
            f"Цена: {price}\n\n"
            "Теперь отправьте иконку для подарка (изображение)"
        )
    except ValueError:
        await message.answer("❌ Шанс, фейковый шанс и цена должны быть числами (например: 0.3, 0.7 и 150)")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        await state.clear()


@router.message(GiftCreateState.waiting_for_gift_photo)
async def handle_gift_create_photo(message: Message, state: FSMContext):
    from db import create_gift, get_gifts_by_case
    try:
        data = await state.get_data()
        case_id = data['case_id']
        name = data['gift_name']
        chance = data['gift_chance']
        fake_chance = data["gift_fake_chance"]
        price = data["gift_price"]

        # Определяем путь к иконке в зависимости от цены
        if price == 0:
            icon_path = "media/failed.png"
        else:
            icon_path = None

        if message.photo:
            # Если цена не 0, обрабатываем фото как обычно
            if price != 0:
                photo = message.photo[-1]
                photo_file = await message.bot.get_file(photo.file_id)
                photo_bytes = await message.bot.download_file(photo_file.file_path)

                # Create unique gift ID
                gifts = await get_gifts_by_case(case_id)
                gift_id = f"gift-{len(gifts) + 1}-{random.randint(1000, 9999)}"

                input_path = f"temp_{gift_id}.png"
                output_path = f"media/gifts/{gift_id}.png"
                with open(input_path, "wb") as f:
                    f.write(photo_bytes.read())

                await message.answer("⏳ Обрабатываю изображение (удаляю фон)...")

                processed_image = remove_background(Image.open(input_path))
                processed_image.save(output_path)
                icon_path = output_path

                if os.path.exists(input_path):
                    os.remove(input_path)
            else:
                # Если цена 0, игнорируем фото и используем failed.png
                gifts = await get_gifts_by_case(case_id)
                gift_id = f"gift-{len(gifts) + 1}-{random.randint(1000, 9999)}"
                await message.answer("⚠️ Цена подарка 0, используется иконка failed.png (фото проигнорировано)")
        else:
            await message.answer("❌ Пожалуйста, отправьте изображение")
            return

        # Создаем подарок в базе данных
        await create_gift(
            gift_id,
            case_id,
            name,
            "https://example.com/gift",  # Default link, can be changed later
            icon_path,
            chance,
            fake_chance,
            price
        )

        # Update case icon
        case = await get_case_by_id(case_id)
        if case:
            await update_case_icon(case)
            # Update case logo in database
            from db import update_case
            await update_case(case_id, logo=case.get('logo'))

        if price == 0:
            await message.answer("✅ Подарок создан! Использована иконка failed.png (цена 0)")
        else:
            await message.answer("✅ Подарок успешно создан!")

    except Exception as e:
        await message.answer(f"❌ Ошибка при создании подарка: {e}")
    finally:
        await state.clear()


@router.callback_query(F.data.startswith("gift_edit_"))
async def handle_gift_edit(callback: CallbackQuery, state: FSMContext):
    data_parts = callback.data.split("_")
    case_id = data_parts[2]
    gift_id = data_parts[3]
    case = await get_case_by_id(case_id)
    if not case:
        await callback.answer("❌ Кейс не найден")
        return
    gift = get_gift_by_id(case, gift_id)
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
            "Теперь отправьте новую иконку для подарка "
            "(или отправьте 'пропустить', чтобы оставить текущую)"
        )
    except ValueError:
        await message.answer("❌ Шанс, фейковый шанс и цена должны быть числами (например: 0.3, 0.7 и 150)")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        await state.clear()

@router.message(GiftEditState.waiting_for_gift_url)
async def handle_gift_photo_input(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        case_id = data['case_id']
        gift_id = data['gift_id']
        name = data['gift_name']
        chance = data['gift_chance']
        fake_chance = data["gift_fake_chance"]
        price = data["gift_price"]

        # Определяем путь к иконке в зависимости от цены
        if price == 0:
            icon_path = "media/failed.png"
        else:
            icon_path = None

        if message.photo:
            # Если цена не 0, обрабатываем фото как обычно
            if price != 0:
                photo = message.photo[-1]
                photo_file = await message.bot.get_file(photo.file_id)
                photo_bytes = await message.bot.download_file(photo_file.file_path)

                input_path = f"temp_{gift_id}.png"
                output_path = f"media/gifts/{gift_id}.png"
                with open(input_path, "wb") as f:
                    f.write(photo_bytes.read())

                await message.answer("⏳ Обрабатываю изображение (удаляю фон)...")

                processed_image = remove_background(Image.open(input_path))
                processed_image.save(output_path)
                icon_path = output_path

                if os.path.exists(input_path):
                    os.remove(input_path)
            else:
                # Если цена 0, игнорируем фото и используем failed.png
                await message.answer("⚠️ Цена подарка 0, используется иконка failed.png (фото проигнорировано)")

        elif message.text.strip().lower() == "пропустить":
            # При пропуске, если цена 0, устанавливаем failed.png
            if price == 0:
                icon_path = "media/failed.png"
                await message.answer("⚠️ Цена подарка 0, используется иконка failed.png")
            # Если цена не 0, оставляем текущую иконку (icon_path останется None)

        else:
            await message.answer("❌ Пожалуйста, отправьте изображение или напишите 'пропустить'")
            return

        # Обновляем данные подарка в базе данных
        from db import update_gift, update_case
        case = await get_case_by_id(case_id)
        if case:
            gift = get_gift_by_id(case, gift_id)
            if gift:
                # Update gift in database
                update_kwargs = {
                    'name': name,
                    'chance': chance,
                    'fake_chance': fake_chance,
                    'price': price
                }
                # Обновляем иконку только если она была определена
                if icon_path is not None:
                    update_kwargs['img'] = icon_path

                await update_gift(gift_id, **update_kwargs)

                # Update local gift object for update_case_icon
                gift.update(update_kwargs)
                await update_case_icon(case)
                # Update case logo in database
                await update_case(case_id, logo=case.get('logo'))

                if price == 0:
                    await message.answer("✅ Подарок обновлён! Использована иконка failed.png (цена 0)")
                else:
                    await message.answer("✅ Подарок обновлён!")
            else:
                await message.answer("❌ Подарок не найден")
        else:
            await message.answer("❌ Кейс не найден")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    finally:
        await state.clear()


@router.message(GiftEditState.waiting_for_gift_url)
async def handle_gift_url_input(message: Message, state: FSMContext):
    from db import update_gift
    try:
        data = await state.get_data()
        case_id = data['case_id']
        gift_id = data['gift_id']
        name = data['gift_name']
        chance = data['gift_chance']
        fake_chance = data["gift_fake_chance"]
        price = data["gift_price"]
        new_url = message.text.strip() if message.text.strip().lower() != 'пропустить' else None
        case = await get_case_by_id(case_id)
        if case:
            gift = get_gift_by_id(case, gift_id)
            if gift:
                # Update gift in memory for icon creation
                gift['name'] = name
                gift['chance'] = chance
                gift["price"] = price
                gift["fake_chance"] = fake_chance
                if new_url:
                    gift['link'] = new_url
                    # Update in database
                    await update_gift(gift_id, name=name, chance=chance, price=price, fake_chance=fake_chance, link=new_url)
                    # Запускаем создание иконки в фоне
                    asyncio.create_task(create_gift_icon_with_notification(message.bot, gift, case, message.chat.id))
                    await message.answer("⏳ Создаю иконку из ссылки... Это может занять несколько секунд")
                else:
                    # Update in database without link
                    await update_gift(gift_id, name=name, chance=chance, price=price, fake_chance=fake_chance)
                    await message.answer("✅ Подарок обновлен (ссылка не изменена)!")
            else:
                await message.answer("❌ Подарок не найден")
        else:
            await message.answer("❌ Кейс не найден")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    await state.clear()

async def create_gift_icon_with_notification(bot: Bot, gift, case, chat_id):
    from db import update_gift, update_case
    try:
        await create_gift_icon(gift, take_screenshot_and_process)
        await update_case_icon(case)
        # Update gift image in database
        await update_gift(gift['id'], img=gift.get('img'))
        # Update case logo in database
        await update_case(case['id'], logo=case.get('logo'))
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
