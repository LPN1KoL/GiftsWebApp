from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl
import json
import asyncio
import threading
import os
from utils import send_queue
from db import get_user_balance_sync, get_user_profile_data_sync
from db import get_user, update_user_balance_and_gifts
from cases import try_open_case_sync
from utils import send_plus_prompt
from bot import main as bot_main
from api import send_win_notification_to_admin_sync

HOST = "0.0.0.0"
HTTP_PORT = 8080
HTTPS_PORT = 443

SSL_CERT = "/etc/letsencrypt/live/giftsapp.ddns.net/fullchain.pem"
SSL_KEY = "/etc/letsencrypt/live/giftsapp.ddns.net/privkey.pem"

# --- Роутинг ---
def handle_plus(data):
    user_id = data.get("user_id")
    if not user_id:
        return 400, {"error": "Missing 'user_id'"}
    print("Попытка отправить сообщение боту:", user_id)
    send_queue.put_nowait(user_id)
    return 200, {"ok": True}

def handle_get_balance(data):
    user_id = data.get("user_id")
    if not user_id:
        return 400, {"error": "Missing 'user_id'"}

    balance = get_user_balance_sync(user_id)
    return 200, {"balance": balance}
    
def handle_open_case(data):
    user_id = data.get("user_id")
    case_id = data.get("case_id")
    if not user_id:
        return 400, {"error": "Missing 'user_id'"}

    result = try_open_case_sync(
        user_id,
        case_id,
        get_user,
        update_user_balance_and_gifts,
        send_win_notification_to_admin_sync
    )
    if "error" in result:
        return 400, {"error": result["error"]}

    return 200, result

def handle_get_profile(data):
    user_id = data.get("user_id")
    if not user_id:
        return 400, {"error": "Missing 'user_id'"}

    try:
        profile_data = get_user_profile_data_sync(user_id)
        # Вернуть все поля
        return 200, {
            "balance": profile_data.get("balance", 0),
            "username": profile_data.get("username", "unknown"),
            "avatar": profile_data.get("avatar"),
            "gifts": profile_data.get("gifts", [])
        }
    except Exception as e:
        print(f"Ошибка получения профиля: {e}")
        return 500, {"error": "Internal server error"}


ROUTES = {
    "/api/plus": handle_plus,
    "/api/get_profile": handle_get_profile,
    "/api/get_balance": handle_get_balance,
    "/api/open_case": handle_open_case,
}


# --- Обработчик HTTP ---
class MyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/', '/index.html']:
            self.path = '/templates/main.html'
        return super().do_GET()

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "Invalid JSON"}')
            return

        handler = ROUTES.get(self.path)
        if handler:
            try:
                status, response = handler(data)
            except Exception as e:
                print("Ошибка в обработчике:", e)
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b'{"error": "Internal server error"}')
                return
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "Unknown endpoint"}')

# --- Запуск ---
def run_server():
    try:
        if not os.path.isfile(SSL_CERT) or not os.path.isfile(SSL_KEY):
            raise FileNotFoundError("SSL-сертификаты не найдены, fallback на HTTP")

        httpd = HTTPServer((HOST, HTTPS_PORT), MyHandler)

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=SSL_CERT, keyfile=SSL_KEY)
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        print(f"Сервер ЗАПУЩЕН на https://{HOST}:{HTTPS_PORT}")
    except Exception as e:
        print("❌ Не удалось запустить HTTPS:", e)
        httpd = HTTPServer((HOST, HTTP_PORT), MyHandler)
        print(f"Сервер fallback на http://{HOST}:{HTTP_PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен")
    finally:
        httpd.server_close()

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    asyncio.run(bot_main())
