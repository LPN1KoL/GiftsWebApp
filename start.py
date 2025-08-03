#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl
import os

# Конфигурация
HOST = "0.0.0.0"
HTTP_PORT = 8080
HTTPS_PORT = 443
SSL_CERT = "/etc/letsencrypt/live/giftsapp.ddns.net/fullchain.pem"
SSL_KEY = "/etc/letsencrypt/live/giftsapp.ddns.net/privkey.pem"

class MyHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(os.path.dirname(__file__)), **kwargs)
    
    def do_GET(self):
        # Перенаправляем корневой путь на templates/index.html
        if self.path in ['/', '/index.html']:
            self.path = '/templates/main.html'

        return super().do_GET()
    
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

def run_server():
    # Проверяем наличие SSL сертификатов
    ssl_enabled = os.path.exists(SSL_CERT) and os.path.exists(SSL_KEY)
    
    if ssl_enabled:
        # Настраиваем HTTPS сервер с использованием SSLContext
        httpd = HTTPServer((HOST, HTTPS_PORT), MyHandler)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=SSL_CERT, keyfile=SSL_KEY)
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        print(f"Сервер запущен на https://{HOST}:{HTTPS_PORT}")
    else:
        # Запускаем обычный HTTP сервер
        httpd = HTTPServer((HOST, HTTP_PORT), MyHandler)
        print(f"Сервер запущен на http://{HOST}:{HTTP_PORT} (SSL не настроен)")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен")
    finally:
        httpd.server_close()

if __name__ == "__main__":
    run_server()