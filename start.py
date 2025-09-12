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
from db import get_user_balance, get_user_profile_data
from db import get_user, update_user_balance_and_gifts
from cases import try_open_case
from bot import main as bot_main
from api import *
import json

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
app.mount("/templates", StaticFiles(directory="templates"), name="templates")
app.mount("/data", StaticFiles(directory="data"), name="data")
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


# --- Роутинг ---
@app.get("/", response_class=HTMLResponse)
@app.get("/main", response_class=HTMLResponse)
async def serve_main(request: Request):
    case_id = request.query_params.get("case_id")
    if case_id:
        print(f"Запрошен case_id: {case_id}")
        data = await get_case_complete_data(case_id)
        if data:
            return templates.TemplateResponse("main.html", {"request": request, "case_id": case_id, "gifts": data["gifts"], "random_gifts": data["random_gifts"], "case_data": data["case_data"]})
        else:
            raise HTTPException(status_code=404, detail="Case not found")
    else:
        data = await get_case_complete_data("case-1")
        if data:
            return templates.TemplateResponse("main.html", {"request": request, "case_id": "case-1", "gifts": data["gifts"], "random_gifts": data["random_gifts"], "case_data": data["case_data"]})
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


@app.get("/{filename}")
async def serve_static_files(filename: str):
    # Проверяем существование файла в templates
    templates_path = os.path.join("templates", filename)
    if os.path.isfile(templates_path):
        return FileResponse(templates_path)

    # Проверяем существование файла в static
    static_path = os.path.join("static", filename)
    if os.path.isfile(static_path):
        return FileResponse(static_path)

    # Если файл не найден
    raise HTTPException(status_code=404, detail="File not found")


@app.get("/data/cases.json")
async def load_cases():
    try:
        return FileResponse('/data/cases.json')
    except:
        # Если файл не найден
        raise HTTPException(status_code=404, detail="File not found")


@app.post("/api/get_balance")
async def handle_get_balance(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing 'user_id'")

    balance = await get_user_balance(user_id)
    return {"balance": balance}


@app.post("/api/open_case")
async def handle_open_case(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    case_id = data.get("case_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing 'user_id'")

    result = await try_open_case(
        user_id,
        case_id,
        get_user,
        update_user_balance_and_gifts,
        send_win_notification_to_admin
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@app.post("/api/get_profile")
async def handle_get_profile(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing 'user_id'")

    try:
        profile_data = await get_user_profile_data(user_id)
        return {
            "balance": profile_data.get("balance", 0),
            "gifts": profile_data.get("gifts", [])
        }
    except Exception as e:
        print(f"Ошибка получения профиля: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# --- Запуск ---
async def run_server():
    ssl_cert = "/etc/letsencrypt/live/giftsapp.ddns.net/fullchain.pem"
    ssl_key = "/etc/letsencrypt/live/giftsapp.ddns.net/privkey.pem"

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
    await server.serve()

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
