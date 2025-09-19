import asyncio
import threading
import signal
from start import run_server
from bot import main as bot_main

def run_server_thread(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_server())

if __name__ == "__main__":
    server_loop = asyncio.new_event_loop()
    server_thread = threading.Thread(target=run_server_thread, args=(server_loop,), daemon=True)
    server_thread.start()

    loop = asyncio.get_event_loop()

    def stop_all():
        print("SIGINT received, stopping...")
        for task in asyncio.all_tasks(loop):
            task.cancel()
        server_loop.call_soon_threadsafe(server_loop.stop)
        loop.stop()

    loop.add_signal_handler(signal.SIGINT, stop_all)

    try:
        loop.run_until_complete(bot_main())
    except asyncio.CancelledError:
        pass
