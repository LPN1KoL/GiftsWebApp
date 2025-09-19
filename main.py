import threading
import asyncio
import signal
import sys
from start import run_server
from bot import main as bot_main

stop_event = threading.Event()

def run_server_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_server())
    finally:
        loop.close()

def signal_handler(sig, frame):
    print("Stopping...")
    stop_event.set()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    server_thread = threading.Thread(target=run_server_thread, daemon=True)
    server_thread.start()

    try:
        asyncio.run(bot_main())
    except KeyboardInterrupt:
        print("Bot stopped")
