import asyncio
from aiogram import Bot, Dispatcher
from handlers import router
from db import init_db
from utils import queue_watcher
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")

async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await init_db()
    asyncio.create_task(queue_watcher(bot))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
