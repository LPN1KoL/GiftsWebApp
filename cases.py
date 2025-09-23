import json
import os
import random
import asyncio
import threading


def load_cases():
    if os.path.exists("data/cases.json"):
        with open("data/cases.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_cases(cases):
    os.makedirs("data", exist_ok=True)
    with open("data/cases.json", "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)

async def update_case_icon(case):
    if not case['gifts']:
        return
    rarest_gift = min(case['gifts'], key=lambda x: x['chance'])
    if rarest_gift.get('img'):
        case['logo'] = rarest_gift['img']
        print(f"✅ Иконка кейса {case['id']} обновлена: {rarest_gift['img']}")

async def create_gift_icon(gift, screenshot_func):
    if gift.get('link'):
        try:
            os.makedirs("media/gifts", exist_ok=True)
            output_path = f"media/gifts/{gift['id']}.png"
            await asyncio.to_thread(
                screenshot_func,
                gift['link'], 
                output_path,
                crop_x=527,
                crop_y=120,
                crop_size=255
            )
            t = threading.Thread(target=screenshot_func, args=(gift['link'], output_path, 527, 120, 255))
            t.start()
            gift['img'] = f"/{output_path}"
            print(f"✅ Иконка подарка {gift['id']} создана: {output_path}")
        except Exception as e:
            print(f"❌ Ошибка при создании иконки подарка {gift['id']}: {e}")

def get_gift_info_by_ids(gifts_json):
    try:
        with open("data/cases.json", "r", encoding="utf-8") as f:
            cases = json.load(f)
    except Exception:
        return []
    gift_info = {gift["id"]: gift for case in cases for gift in case["gifts"]}
    gifts_ids = json.loads(gifts_json) if gifts_json else []
    user_gifts = [gift_info[gid] for gid in gifts_ids if gid in gift_info]
    return user_gifts

def get_case_by_id(case_id):
    cases = load_cases()
    case = next((c for c in cases if c["id"] == case_id), None)
    return case

def get_gift_by_id(case, gift_id):
    return next((g for g in case["gifts"] if g["id"] == gift_id), None)


async def try_open_case(user_id, case_id, get_user, update_user_balance_and_gifts):
    cases = load_cases()
    case = next((c for c in cases if c["id"] == case_id), None)
    if not case:
        return {"error": "Кейс не найден"}
    price = case["price"]
    row = await get_user(user_id)
    if not row:
        return {"error": "Пользователь не найден"}
    balance, gifts_raw = row
    if balance < price:
        return {"error": f"Недостаточно средств"}
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
    new_balance = balance - price
    gifts_list = json.loads(gifts_raw) if gifts_raw else []
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
    cases = load_cases()
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
    cases = load_cases()
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