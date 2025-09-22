import requests
import aiohttp
import base64
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

def send_notification_to_admin_sync(user_id: int, data):
    """
    Синхронная функция для отправки уведомления администратору
    """
    try:
        # Получаем информацию о пользователе
        get_chat_url = f"https://api.telegram.org/bot{API_TOKEN}/getChat"
        response = requests.post(get_chat_url, json={"chat_id": user_id}, timeout=10)
        response.raise_for_status()
        
        info = response.json()
        if info.get('ok'):
            username = info['result'].get('username')
            user_mention = f"@{username}" if username else str(user_id)
        else:
            user_mention = str(user_id)
            
    except requests.RequestException:
        user_mention = str(user_id)
    
    # Формируем текст сообщения
    message_text = (
        f"🎉 Кто-то подал заявку на вывод!\n\n"
        f"👤 Пользователь: {user_mention}\n"
        f"🎁 Приз: {data['name']}\n\n"
        f"Отправьте подарок этому пользователю!"
    )
    
    # Отправляем сообщение администратору
    try:
        send_message_url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
        requests.post(send_message_url, json={
            "chat_id": ADMIN_ID,
            "text": message_text
        }, timeout=10)
    except requests.RequestException:
        print("Failed to send notification to admin")
        pass

async def send_notification_to_admin(user_id: int, data):
    """
    Асинхронная обертка для синхронной функции
    """
    await asyncio.to_thread(send_notification_to_admin_sync, user_id, data)


def take_screenshot_and_process(url, output_path, crop_x, crop_y, crop_size):
    print(f"⚠️  Скриншот не сделан (функция не импортирована): {url}")
    try:
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='red')
        img.save(output_path)
    except Exception:
        pass


async def get_user_avatar_base64(user_id: int, size: int = 256) -> str:
    """
    Получает аватар пользователя и конвертирует в base64.
    Если аватара нет или произошла ошибка - возвращает base64 черного квадрата.
    Всё выполняется в памяти без сохранения на диск.

    Args:
        user_id: ID пользователя Telegram
        size: Размер выходного изображения в пикселях (квадрат)

    Returns:
        Base64 строка с data URL (data:image/jpeg;base64,...)
    """
    try:
        print(f"Начинаем получение аватара для user_id: {user_id}")

        # Создаем новую сессию aiohttp для избежания конфликта контекстов
        async with aiohttp.ClientSession() as session:
            # Пытаемся получить аватар пользователя
            try:
                user_profile_url = f"https://api.telegram.org/bot{API_TOKEN}/getUserProfilePhotos?user_id={user_id}&limit=1"
                async with session.get(user_profile_url) as profile_response:
                    if profile_response.status == 200:
                        profile_data = await profile_response.json()
                        if profile_data.get('ok') and profile_data['result']['total_count'] > 0:
                            file_id = profile_data['result']['photos'][0][0]['file_id']

                            # Получаем информацию о файле
                            file_info_url = f"https://api.telegram.org/bot{API_TOKEN}/getFile?file_id={file_id}"
                            async with session.get(file_info_url) as file_response:
                                if file_response.status == 200:
                                    file_data = await file_response.json()
                                    if file_data.get('ok'):
                                        file_path = file_data['result']['file_path']
                                        file_download_url = f"https://api.telegram.org/file/bot{API_TOKEN}/{file_path}"

                                        # Скачиваем изображение
                                        async with session.get(file_download_url) as download_response:
                                            if download_response.status == 200:
                                                image_data = await download_response.read()
                                                base64_data = base64.b64encode(image_data).decode('utf-8')
                                                return f"data:image/jpeg;base64,{base64_data}"
            except Exception as alt_error:
                print(f"Альтернативный метод failed: {alt_error}")

        print("Создаем черный квадрат...")
        # Если аватар не найден - создаем черный квадрат
        with BytesIO() as buffer:
            black_image = Image.new('RGB', (size, size), color='black')
            black_image.save(buffer, format='JPEG', quality=95)
            base64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            print(f"Создан черный квадрат, base64 длина: {len(base64_data)}")
            return f"data:image/jpeg;base64,{base64_data}"

    except Exception as e:
        print(f"Произошла ошибка: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

        # Создаем черный квадрат при любой ошибке
        with BytesIO() as buffer:
            black_image = Image.new('RGB', (size, size), color='black')
            black_image.save(buffer, format='JPEG', quality=95)
            base64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_data}"


def check_subscription_sync(user_id: int, channel_id: int):
    """
    Упрощенная синхронная функция проверки подписки
    Возвращает только boolean результат
    """
    try:
        get_member_url = f"https://api.telegram.org/bot{API_TOKEN}/getChatMember"
        response = requests.post(
            get_member_url,
            json={
                "chat_id": channel_id,
                "user_id": user_id
            },
            timeout=10
        )
        response.raise_for_status()
        
        member_info = response.json()
        if member_info.get('ok'):
            status = member_info['result']['status']
            return status != 'left' and status != 'kicked'
        
        return False
        
    except:
        return False

async def check_subscription(user_id: int, channel_id: int):
    """
    Асинхронная обертка для упрощенной версии
    """
    return await asyncio.to_thread(check_subscription_sync, user_id, channel_id)