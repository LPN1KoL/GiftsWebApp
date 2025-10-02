from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import sys
import os

def take_screenshot(url, output_path="screenshot.png"):
    # Настройки Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")  # Стандартный размер окна
    
    try:
        # Запускаем браузер
        driver = webdriver.Chrome(options=chrome_options)
        
        # Открываем страницу
        driver.get(url)
        
        # Ждем загрузки страницы
        time.sleep(3)
        
        # Делаем скриншот
        driver.save_screenshot(output_path)
        
        # Закрываем браузер
        driver.quit()
        
        print(f"Скриншот сохранен как: {output_path}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python screenshot.py <URL> [output_file]")
        print("Пример: python screenshot.py https://example.com my_screenshot.png")
        sys.exit(1)
    
    url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "screenshot.png"
    
    take_screenshot(url, output_file)