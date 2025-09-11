import asyncio
from aiogram import Bot, Dispatcher
from handlers import router
from db import init_db
from utils import queue_watcher

API_TOKEN = "8008525871:AAFpPTPQbsF661zdGXSNRsriquhiqn-VpKQ"


async def main():
    try:
        bot = Bot(token=API_TOKEN)
        dp = Dispatcher()
        dp.include_router(router)
        await init_db()
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("Bot stopped")

if __name__ == "__main__":
    asyncio.run(main())
