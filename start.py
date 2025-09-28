import random
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import ssl
import asyncio
import os
import sys
from db import get_user_balance, get_user_profile_data, update_user_tasks, get_user_tasks, get_profile_data_and_tasks, update_user_balance
from db import get_user, update_user_balance_and_gifts
from cases import try_open_case, try_sell_gift, try_get_gift
from bot import main as bot_main
from api import *
import json
from urllib.parse import parse_qs, urlencode
import hmac
import hashlib
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
app = FastAPI(title="Gifts App API")
templates = Jinja2Templates(directory="templates")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтирование статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")


# --- Вспомогательные функции ---
async def load_cases_data():
    try:
        with open("data/cases.json", "r", encoding="utf-8") as f:
            cases = json.load(f)
            
            # Фильтруем только нужные поля
            filtered_cases = []
            for case in cases:
                filtered_case = {
                    "id": case.get("id"),
                    "name": case.get("name"),
                    "price": case.get("price"),
                    "logo": case.get("logo"),
                    "category": case.get("category")
                }
                filtered_cases.append(filtered_case)
            
            return filtered_cases
            
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Ошибка загрузки cases.json: {e}")
        return []
    

async def get_case_complete_data(case_id, random_length=32):
    """
    Универсальная функция для получения всех данных о кейсе за одно чтение файла
    :param case_id: ID кейса
    :param random_length: Количество случайных подарков (по умолчанию 32)
    :return: Словарь с тремя ключами: case_data, gifts, random_gifts
             или None если кейс не найден
    """
    try:
        with open("data/cases.json", "r", encoding="utf-8") as f:
            cases = json.load(f)
            
            # Ищем нужный кейс
            target_case = None
            for case in cases:
                if case.get("id") == case_id:
                    target_case = case
                    break
            
            if not target_case:
                return None
            
            result = {}
            gifts_list = target_case.get("gifts", [])
            
            # 1. Данные кейса
            result["case_data"] = {
                "id": target_case.get("id"),
                "name": target_case.get("name"),
                "price": target_case.get("price"),
                "logo": target_case.get("logo")
            }
            
            # 2. Список всех подарков с fake_chance
            result["gifts"] = []
            for gift in gifts_list:
                if gift.get("price") != 0:
                    result["gifts"].append({
                        "id": gift.get("id"),
                        "name": gift.get("name"),
                        "image": gift.get("img"),  
                        "price": gift.get("price"),
                        "chance": gift.get("fake_chance")
                    })
            
            # 3. Список из 32 случайных подарков
            result["random_gifts"] = []
            
            if gifts_list:  # Если есть подарки в кейсе
                for _ in range(random_length):
                    # Выбираем подарок на основе шансов
                    rnd = random.random()
                    cumulative = 0
                    selected_gift = None

                    for gift in gifts_list:
                        chance = gift.get("chance")
                        if chance is None:
                            continue
                        cumulative += chance
                        if rnd <= cumulative:
                            selected_gift = gift
                            break
                    
                    if not selected_gift:
                        selected_gift = gifts_list[-1]

                    result["random_gifts"].append({
                        "id": selected_gift.get("id"),
                        "name": selected_gift.get("name"),
                        "image": selected_gift.get("img"),
                        "price": selected_gift.get("price"),
                        "chance": selected_gift.get("fake_chance")
                    })
            
            return result
            
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Ошибка загрузки cases.json: {e}")
        return None


async def verify_telegram_webapp_data(init_data: str):
    """
    Полная проверка Telegram WebApp init data
    """
    if not init_data:
        raise HTTPException(status_code=401, detail="Init data required")
    
    try:
        # Парсим данные
        parsed_data = parse_qs(init_data)
        
        # Извлекаем hash
        hash_value = parsed_data.get("hash", [None])[0]
        if not hash_value:
            raise HTTPException(status_code=401, detail="Hash not found")
        
        # Удаляем hash из данных для проверки
        parsed_data.pop("hash", None)
        
        # Сортируем параметры и создаем data_check_string
        data_check_parts = []
        for key in sorted(parsed_data.keys()):
            for value in parsed_data[key]:
                data_check_parts.append(f"{key}={value}")
        
        data_check_string = "\n".join(data_check_parts)
        
        # Создаем секретный ключ
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=os.getenv("API_TOKEN").encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        # Вычисляем ожидаемый hash
        expected_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Сравниваем hash
        if not hmac.compare_digest(hash_value, expected_hash):
            raise HTTPException(status_code=401, detail="Invalid hash")
        
        # Извлекаем user данные
        user_str = parsed_data.get("user", [None])[0]
        if not user_str:
            raise HTTPException(status_code=401, detail="User data not found")
        
        # Парсим user данные
        import json
        user_data = json.loads(user_str)
        
        return user_data
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Verification failed: {str(e)}")


# --- Роутинг ---
@app.get("/", response_class=HTMLResponse)
@app.get("/main", response_class=HTMLResponse)
async def serve_main(request: Request):
    case_id = request.query_params.get("case_id")
    if case_id:
        data = await get_case_complete_data(case_id)
        if data:
            return templates.TemplateResponse("main.html", {"request": request, "case_id": case_id, "gifts": data["gifts"], "random_gifts": {"random_gifts": data["random_gifts"]}, "case_data": data["case_data"]})
        else:
            raise HTTPException(status_code=404, detail="Case not found")
    else:
        data = await get_case_complete_data("case-1")
        if data:
            return templates.TemplateResponse("main.html", {"request": request, "case_id": "case-1", "gifts": data["gifts"], "random_gifts": {"random_gifts": data["random_gifts"]}, "case_data": data["case_data"]})
        else:
            raise HTTPException(status_code=404, detail="Case not found")
 

@app.get("/cases", response_class=HTMLResponse)
async def cases_page(request: Request):
    cases_data = await load_cases_data()
    
    # Разделяем кейсы по категориям
    basic_cases = [case for case in cases_data if case.get('category') == 'basic']
    allin_cases = [case for case in cases_data if case.get('category') == 'allin']
    
    return templates.TemplateResponse(
        "cases.html",
        {
            "basic_cases": basic_cases,
            "allin_cases": allin_cases,
            "request": request
        }
    )


@app.get("/profile", response_class=HTMLResponse)
async def serve_profile():
    return FileResponse("templates/profile.html")


@app.get("/media/{filename}")
async def get_media_file(filename):
    try:
        return FileResponse(os.path.join('/media', filename))
    except:
        # Если файл не найден
        raise HTTPException(status_code=404, detail="File not found")


@app.get("/favicon.ico")
async def get_favicon():
    return HTTPException(status_code=404, detail="Not found")


@app.get("/{filename}")
async def serve_static_files(filename: str):
    static_path = os.path.join("static", filename)
    if os.path.isfile(static_path):
        return FileResponse(static_path)

    # Если файл не найден
    raise HTTPException(status_code=404, detail="File not found")


#--- API эндпоинты ---
@app.post("/api/open_case")
async def handle_open_case(request: Request):
    data = await request.json()
    user_data = await verify_telegram_webapp_data(data.get("init_data"))
    user_id = user_data.get("id")
    case_id = data.get("case_id")
    if not user_id:
        raise HTTPException(status_code=404, detail="Missing user_data")

    result = await try_open_case(
        user_id,
        case_id,
        get_user,
        update_user_balance_and_gifts
    )

    if not "error" in result:

        tasks = await get_user_tasks(user_id)
        if tasks["last_visit"] != int(datetime.now().timestamp()) // 86400:
            await update_user_tasks(user_id, last_visit=int(datetime.now().timestamp()) // 86400, today_opened_cases=1)
        else:
            await update_user_tasks(user_id, today_opened_cases=tasks["today_opened_cases"] + 1)

        if tasks.get("today_opened_cases", 0) == 9:
            await update_user_balance(user_id, 10)  # Бонус 10 монет
            
        if tasks.get("today_opened_cases", 0) == 24:
            await update_user_balance(user_id, 25)  # Бонус 25 монет

    return JSONResponse(status_code=200, content=result)


@app.post("/api/sell_gift")
async def handle_sell_gift(request: Request):
    data = await request.json()
    init_data = data.get("initData")
    gift_id = data.get("gift_id")
    if not init_data or not gift_id:
        raise HTTPException(status_code=400, detail="Missing 'initData' or 'gift_id'")

    user_data = await verify_telegram_webapp_data(init_data)
    user_id = user_data.get("id")
    if not user_id:
        raise HTTPException(status_code=404, detail="Missing user_data")

    await try_sell_gift(user_id, gift_id, get_user, update_user_balance_and_gifts)

    try:
        return JSONResponse(status_code=200, content={"success": True})
    except Exception as e:
        print(f"Ошибка при продаже подарка: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/get_profile")
async def handle_get_profile(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing 'user_id'")

    try:
        profile_data = await get_profile_data_and_tasks(user_id)
        

        # Получаем всю информацию о подарках пользователя
        gifts_ids = json.loads(profile_data.get("gifts_json", "[]"))
        gifts_info = []
        with open("data/cases.json", "r", encoding="utf-8") as f:
            cases = json.load(f)
            all_gifts = {}
            for case in cases:
                for gift in case.get("gifts", []):
                    all_gifts[gift["id"]] = {
                        "id": gift["id"],
                        "name": gift["name"],
                        "image": gift["img"],
                        "price": gift["price"]
                    }
            for gift_id in gifts_ids:
                gift_data = all_gifts.get(gift_id)
                if gift_data:
                    gifts_info.append(gift_data)

        balance = profile_data.get("balance", 0)

        if profile_data.get("everyday_visits", 0) >= 25:
            everyday_visits = 25
            await update_user_tasks(user_id, everyday_visits=0)
            await update_user_balance(user_id, 30)
            balance += 30  # Бонус 30 монет
        else:
            everyday_visits = profile_data.get("everyday_visits", 0)
        
        
        subscribed = profile_data.get("subscribed", False)
        if not subscribed:
            if await check_subscription(user_id, -1002579027468):  # Проверяем подписку на канал
                await update_user_tasks(user_id, subscribed=True)
                await update_user_balance(user_id, 5)  # Бонус 5 монет
                balance += 5
                subscribed = True

        return {
            "balance": balance,
            "gifts": gifts_info,
            "everyday_visits": everyday_visits,
            "today_opened_cases": profile_data.get("today_opened_cases", 0),
            "subscribed": subscribed
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/get_gift")
async def handle_get_gift(request: Request):
    data = await request.json()
    gift_id = data.get("gift_id")
    initData = data.get("initData")
    if not (initData or gift_id):
        raise HTTPException(status_code=400, detail="Missing 'initData' or 'gift_id'")
    
    user_data = await verify_telegram_webapp_data(initData)
    user_id = user_data.get("id")
    if not user_id:
        raise HTTPException(status_code=404, detail="Missing user_data")
    
    try:
        result = await try_get_gift(user_id, gift_id, get_user, send_notification_to_admin, update_user_balance_and_gifts)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")
    

@app.post("/api/update_last_visit")
async def handle_update_last_visit(request: Request):
    data = await request.json()
    initData = data.get("init_data")
    if not initData:
        raise HTTPException(status_code=400, detail="Missing 'init_data'")
    
    user_data = await verify_telegram_webapp_data(initData)
    user_id = user_data.get("id")
    if not user_id:
        raise HTTPException(status_code=404, detail="Missing user_data")
    
    try:
        tasks = await get_user_tasks(user_id)
        # Обновляем last_visit
        today = int(datetime.now().timestamp()) // 86400
        if tasks["last_visit"] == today - 1:
            await update_user_tasks(user_id, last_visit=today, everyday_visits=tasks["everyday_visits"] + 1, today_opened_cases=0)
        elif tasks["last_visit"] == today:
            pass
        else:
            await update_user_tasks(user_id, last_visit=today, everyday_visits=1, today_opened_cases=0)
        
        return JSONResponse(status_code=200, content={"success": True})
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/404")
async def handle_404():
    return JSONResponse(status_code=200, content={"error": "Page not found"})


@app.post("/api/donate")
async def handle_donate(request: Request):
    try:
        data = await request.json()
        user_id = data.get("user_id")
        print(user_id)
        await send_notif_to_user(user_id)
        return JSONResponse(status_code=200, content={"success": True})
    except:
        raise HTTPException(status_code=500, detail="Internal server error")


# --- Запуск ---
async def run_server():
    ssl_cert = f"/etc/letsencrypt/live/{os.getenv('DOMAIN')}/fullchain.pem"
    ssl_key = f"/etc/letsencrypt/live/{os.getenv('DOMAIN')}/privkey.pem"

    ssl_context = None
    port = 8080

    if os.path.isfile(ssl_cert) and os.path.isfile(ssl_key):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(ssl_cert, ssl_key)
        port = 443
        print(f"Сервер ЗАПУЩЕН на https://0.0.0.0:{port}")
    else:
        print("SSL-сертификаты не найдены, fallback на HTTP")
        print(f"Сервер fallback на http://0.0.0.0:{port}")

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=port,
        ssl_certfile=ssl_cert if ssl_context else None,
        ssl_keyfile=ssl_key if ssl_context else None,
    )

    server = uvicorn.Server(config)
    try:
        await server.serve()
    except KeyboardInterrupt:
        sys.exit(0)

async def main():
    # Запускаем сервер и бота параллельно
    try:
        server_task = asyncio.create_task(run_server())
        bot_task = asyncio.create_task(bot_main())

        # Ожидаем завершения обеих задач
        await asyncio.gather(server_task, bot_task)
    except KeyboardInterrupt:
        print("Server and Bot stopped")

if __name__ == "__main__":
    asyncio.run(main())
