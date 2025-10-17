import sys
import asyncio
import os
import io
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from rembg import remove
import time
import threading

# Словарь кодовых слов и соответствующих файлов
KEYWORD_IMAGES = {
    "bear": "./media/bear.png",
    "bottle": "./media/bottle.png", 
    "box": "./media/box.png",
    "cacke": "./media/cacke.png",
    "diamond": "./media/diamond.png",
    "flower": "./media/flower.png",
    "flowers": "./media/flowers.png",
    "heart": "./media/heart.png",
    "prize": "./media/prize.png",
    "ring": "./media/ring.png",
    "rocket": "./media/rocket.png",
    "star": "./media/star.png"
}

def take_screenshot_and_process(url, output_path="processed_screenshot.png", crop_x=880, crop_y=118, crop_size=160):
    # Принудительно устанавливаем нужные значения
    crop_x = 880
    crop_y = 118
    crop_size = 160
    
    # Проверяем, является ли URL кодовым словом
    if url in KEYWORD_IMAGES:
        image_path = KEYWORD_IMAGES[url]
        if os.path.exists(image_path):
            # Копируем соответствующее изображение в выходной путь
            with Image.open(image_path) as img:
                img.save(output_path)
            print(f"Использовано изображение по кодовому слову: {output_path}")
            return
        else:
            print(f"Предупреждение: файл {image_path} не найден, продолжаем обычную обработку")
    
    # Настройки Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        # Запускаем браузер
        driver = webdriver.Chrome(options=chrome_options)
        
        # Открываем страницу
        driver.get(url)
        
        # Ждем загрузки страницы
        time.sleep(5)
        
        # Делаем временный скриншот
        temp_file = "temp_screenshot.png"
        driver.save_screenshot(temp_file)
        
        # Закрываем браузер
        driver.quit()
        
        # Обрабатываем изображение
        process_image(temp_file, output_path, crop_x, crop_y, crop_size)
        
        # Удаляем временный файл
        #os.remove(temp_file)
        
        print(f"Обработанный скриншот сохранен как: {output_path}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        if 'driver' in locals():
            driver.quit()

def process_image(input_path, output_path, crop_x, crop_y, crop_size):
    # Открываем изображение
    image = Image.open(input_path)
    
    # Обрезаем изображение
    crop_box = (crop_x, crop_y, crop_x + crop_size, crop_y + crop_size)
    cropped_image = image.crop(crop_box)
    
    # Удаляем фон с помощью rembg
    processed_image = remove_background(cropped_image)
    
    # Сохраняем результат
    processed_image.save(output_path)

def remove_background(image):
    # Конвертируем PIL Image в bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    # Удаляем фон
    result_bytes = remove(img_byte_arr)
    
    # Конвертируем обратно в PIL Image
    result_image = Image.open(io.BytesIO(result_bytes))
    
    return result_image

def sync_task(url, output_file, crop_x, crop_y, crop_size):
    take_screenshot_and_process(url, output_file, crop_x, crop_y, crop_size)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python screenshot.py <URL_или_кодовое_слово>")
        print("Доступные кодовые слова:", ", ".join(KEYWORD_IMAGES.keys()))
        sys.exit(1)
    
    url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "processed_screenshot.png"
    
    crop_x = 527
    crop_y = 120
    crop_size = 255
    
    t = threading.Thread(target=sync_task, args=(url, output_file, crop_x, crop_y, crop_size))
    t.start()
    
send_queue = asyncio.Queue()
payments = {}

async def send_plus_prompt(bot, user_id):
    await bot.send_message(user_id, "Введите сумму пополнения (число):")

async def queue_watcher(bot):
    while True:
        user_id = await send_queue.get()
        print("queue_watcher: отправляю сообщение", user_id)
        await send_plus_prompt(bot, user_id)