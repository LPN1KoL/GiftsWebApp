import asyncio

send_queue = asyncio.Queue()
payments = {}

async def send_plus_prompt(bot, user_id):
    await bot.send_message(user_id, "Введите сумму пополнения (число):")

async def queue_watcher(bot):
    while True:
        user_id = await send_queue.get()
        print("queue_watcher: отправляю сообщение", user_id)
        await send_plus_prompt(bot, user_id)