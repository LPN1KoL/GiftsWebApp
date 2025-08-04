import threading
import asyncio
from start import run_server
from bot import main as bot_main

if __name__ == "__main__":
    print("Стартую сервер и бота...")
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    print("Сервер запущен, стартую бота...")
    asyncio.run(bot_main())