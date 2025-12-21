import json
import os
import random
import asyncio
import threading
from db import get_all_cases_with_gifts, get_case_with_gifts, update_case, create_case, create_gift, update_gift, delete_case, delete_gift


async def load_cases():
    """Load all cases from database"""
    return await get_all_cases_with_gifts()

async def save_cases(cases):
    """Save cases to database (for backward compatibility)"""
    # This function is kept for backward compatibility but updates the database
    # Note: This is a simplified version and may need refinement based on usage patterns
    for case in cases:
        existing_case = await get_case_with_gifts(case['id'])
        if existing_case:
            # Update existing case
            await update_case(
                case['id'],
                category=case.get('category'),
                name=case.get('name'),
                price=case.get('price'),
                logo=case.get('logo'),
                published=case.get('published', False)
            )
            # Update gifts
            for gift in case.get('gifts', []):
                await update_gift(
                    gift['id'],
                    case_id=case['id'],
                    name=gift['name'],
                    link=gift.get('link'),
                    img=gift.get('img'),
                    chance=gift['chance'],
                    fake_chance=gift.get('fake_chance', gift['chance']),
                    price=gift.get('price', 0)
                )
        else:
            # Create new case
            await create_case(
                case['id'],
                case.get('category', 'basic'),
                case.get('name', 'New Case'),
                case.get('price', 100),
                case.get('logo'),
                case.get('published', False)
            )
            # Create gifts
            for gift in case.get('gifts', []):
                await create_gift(
                    gift['id'],
                    case['id'],
                    gift['name'],
                    gift.get('link'),
                    gift.get('img'),
                    gift['chance'],
                    gift.get('fake_chance', gift['chance']),
                    gift.get('price', 0)
                )

async def update_case_icon(case):
    if not case['gifts']:
        return
    # Меняем min на max и ключ с 'chance' на 'price'
    most_expensive_gift = max(case['gifts'], key=lambda x: x.get('price', 0))
    if most_expensive_gift.get('img'):
        case['logo'] = most_expensive_gift['img']
        print(f"✅ Иконка кейса {case['id']} обновлена на основе самого дорогого подарка: {most_expensive_gift['name']} (цена: {most_expensive_gift.get('price', 0)})")

async def create_gift_icon(gift, screenshot_func):
    if gift.get('link'):
        try:
            os.makedirs("media/gifts", exist_ok=True)
            output_path = f"media/gifts/{gift['id']}.png"
            await asyncio.to_thread(
                screenshot_func,
                gift['link'], 
                output_path,
                crop_x=868,
                crop_y=98,
                crop_size=202
            )
            t = threading.Thread(target=screenshot_func, args=(gift['link'], output_path, 527, 120, 255))
            t.start()
            gift['img'] = f"/{output_path}"
            print(f"✅ Иконка подарка {gift['id']} создана: {output_path}")
        except Exception as e:
            print(f"❌ Ошибка при создании иконки подарка {gift['id']}: {e}")

async def get_gift_info_by_ids(gifts_json):
    """Get gift information by IDs from database"""
    try:
        cases = await load_cases()
    except Exception:
        return []
    gift_info = {gift["id"]: gift for case in cases for gift in case["gifts"]}
    gifts_ids = json.loads(gifts_json) if gifts_json else []
    user_gifts = [gift_info[gid] for gid in gifts_ids if gid in gift_info]
    return user_gifts

async def get_case_by_id(case_id):
    """Get a case by ID from database"""
    return await get_case_with_gifts(case_id)

def get_gift_by_id(case, gift_id):
    """Get a gift by ID from case"""
    return next((g for g in case["gifts"] if g["id"] == gift_id), None)


async def try_open_case(user_id, case_id, demo, get_user, update_user_balance_and_gifts):
    case = await get_case_by_id(case_id)
    if not case:
        return {"error": "Кейс не найден"}
    
    price = case["price"]
    row = await get_user(user_id)
    if not row:
        return {"error": "Пользователь не найден"}
    
    balance, gifts_raw = row
    if not demo and balance < price:
        return {"error": "Недостаточно средств"}
    
    if not demo:
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
    else:
        rnd = random.random()
        cumulative = 0
        selected_gift = None
        for gift in case["gifts"]:
            cumulative += gift["fake_chance"]
            if rnd <= cumulative:
                selected_gift = gift
                break

        if not selected_gift:
            selected_gift = case["gifts"][-1]

    if not demo:
        new_balance = balance - price
        gifts_list = json.loads(gifts_raw) if gifts_raw else []
        if selected_gift.get("price", 0) != 0:
            gifts_list.append(selected_gift["id"])
        await update_user_balance_and_gifts(user_id, new_balance, gifts_list)

    return {
        "gift": {
            "id": selected_gift["id"],
            "name": selected_gift["name"],
            "image": selected_gift["img"],
            "price": selected_gift.get("price", 0)
        }
    }

async def try_sell_gift(user_id, gift_id, get_user, update_user_balance_and_gifts):
    row = await get_user(user_id)
    if not row:
        return {"error": "Пользователь не найден"}
    balance, gifts_raw = row
    gifts_list = json.loads(gifts_raw) if gifts_raw else []
    if gift_id not in gifts_list:
        return {"error": "Подарок не найден в инвентаре"}
    cases = await load_cases()
    gift_info = {gift["id"]: gift for case in cases for gift in case["gifts"]}
    gift = gift_info.get(gift_id)
    if not gift:
        return {"error": "Информация о подарке не найдена"}
    sell_price = gift.get("price", 0)
    new_balance = balance + sell_price
    gifts_list.remove(gift_id)
    await update_user_balance_and_gifts(user_id, new_balance, gifts_list)
    return {"success": True}


async def try_get_gift(user_id, gift_id, get_user, send_notification_to_admin, update_user_balance_and_gifts):
    row = await get_user(user_id)
    if not row:
        return {"error": "Пользователь не найден"}
    balance, gifts_raw = row
    gifts_list = json.loads(gifts_raw) if gifts_raw else []
    if gift_id not in gifts_list:
        return {"error": "Подарок не найден в инвентаре"}
    cases = await load_cases()
    data = {"name": gift["name"] for case in cases for gift in case["gifts"] if gift["id"] == gift_id}
    if not data:
        return {"error": "Информация о подарке не найдена"}
    try:
        gifts_list.remove(gift_id)
    except ValueError as e:
        return {"error": "Ошибка при удалении подарка из инвентаря"}
    await update_user_balance_and_gifts(user_id, balance, gifts_list)
    await send_notification_to_admin(user_id, data)
    return {"success": True}