import threading
import asyncio
from start import run_server
from bot import main as bot_main

def run_server_thread():
    asyncio.run(run_server())

if __name__ == "__main__":
    print("Стартую сервер и бота...")

    # Запускаем сервер в отдельном потоке
    server_thread = threading.Thread(target=run_server_thread, daemon=True)
    server_thread.start()

    print("Сервер запущен, стартую бота...")

    # Запускаем бота в главном потоке
    asyncio.run(bot_main())
