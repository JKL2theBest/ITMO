from http.server import HTTPServer, BaseHTTPRequestHandler


class RedirectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Отправляем редирект на secret_server с нужными параметрами
        self.send_response(302)
        self.send_header("Location", "http://secret_server/flag?enable=true")
        self.end_headers()


def run_server():
    # Запускаем сервер на всех интерфейсах (0.0.0.0) и порту 11000
    server_address = ("0.0.0.0", 11000)
    httpd = HTTPServer(server_address, RedirectHandler)
    print("Сервер запущен на http://0.0.0.0:11000 - ожидаем визита админа...")
    httpd.serve_forever()


if __name__ == "__main__":
    run_server()
