import threading
import asyncio
from start import run_server
from bot import main as bot_main

def run_server_thread():
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("Server stopped")

if __name__ == "__main__":
    print("Starting server and bot...")

    # Start server in a separate thread
    server_thread = threading.Thread(target=run_server_thread, daemon=True)
    server_thread.start()

    print("Server started, starting bot...")

    # Start bot in the main thread
    asyncio.run(bot_main())
