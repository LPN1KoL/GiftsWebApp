import requests
import os
from aiogram import Bot

API_TOKEN = "8008525871:AAFpPTPQbsF661zdGXSNRsriquhiqn-VpKQ"
ADMIN_ID = 849307631

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

async def download_user_avatar(bot: Bot, user_id):
    photos = await bot.get_user_profile_photos(user_id, limit=1)
    if photos.total_count > 0:
        file_id = photos.photos[0][0].file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        destination_folder = "profile_picture"
        os.makedirs(destination_folder, exist_ok=True)
        destination_path = os.path.join(destination_folder, f"{user_id}.png")
        await bot.download_file(file_path, destination_path)
        return destination_path
    return None

def take_screenshot_and_process(url, output_path, crop_x, crop_y, crop_size):
    print(f"⚠️  Скриншот не сделан (функция не импортирована): {url}")
    try:
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='red')
        img.save(output_path)
    except Exception:
        pass