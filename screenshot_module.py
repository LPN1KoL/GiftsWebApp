from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
import time
import sys
import os
from rembg import remove
import io

def take_screenshot_and_process(url, output_path="processed_screenshot.png", crop_x=868, crop_y=98, crop_size=202):
    # Настройки Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=640,360")
    
    try:
        # Запускаем браузер
        driver = webdriver.Chrome(options=chrome_options)
        
        # Открываем страницу
        driver.get(url)
        
        # Ждем загрузки страницы
        time.sleep(3)
        
        # Делаем временный скриншот
        temp_file = "temp_screenshot.png"
        driver.save_screenshot(temp_file)
        
        # Закрываем браузер
        driver.quit()
        
        # Обрабатываем изображение
        process_image(temp_file, output_path, crop_x, crop_y, crop_size)
        
        # Удаляем временный файл
        os.remove(temp_file)
        
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