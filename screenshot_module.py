from playwright.sync_api import sync_playwright
from PIL import Image
import time
import sys
import os
from rembg import remove
import io

def take_screenshot_and_process(url, output_path="processed_screenshot.png", crop_x=868, crop_y=98, crop_size=202):
    try:
        with sync_playwright() as p:
            # Запускаем браузер
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )
            
            # Создаем контекст и страницу
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = context.new_page()
            
            # Открываем страницу
            page.goto(url)
            
            # Ждем загрузки страницы
            page.wait_for_timeout(10000)  # 10 секунд
            
            # Делаем временный скриншот
            temp_file = "temp_screenshot.png"
            page.screenshot(path=temp_file, full_page=True)
            
            # Закрываем браузер
            browser.close()
            
            # Обрабатываем изображение
            process_image(temp_file, output_path, crop_x, crop_y, crop_size)
            
            # Удаляем временный файл
            os.remove(temp_file)
            
            print(f"Обработанный скриншот сохранен как: {output_path}")
            
    except Exception as e:
        print(f"Ошибка: {e}")

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
    
    # Удаляем фон с другой моделью
    result_bytes = remove(
        img_byte_arr,
        session=rembg.new_session("u2net")  # или "u2netp", "u2net_human_seg"
    )
    
    # Конвертируем обратно в PIL Image
    result_image = Image.open(io.BytesIO(result_bytes))
    
    return result_image

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python screenshot.py <URL>")
        sys.exit(1)
    
    url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "processed_screenshot.png"
    
    crop_x = 868
    crop_y = 98
    crop_size = 202
    
    take_screenshot_and_process(url, output_file, crop_x, crop_y, crop_size)