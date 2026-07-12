import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram.ext import Application

from finanzas.config.settings import settings
from finanzas.interfaces.telegram_bot.handlers import obtener_handlers


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass


def start_health_server() -> None:
    port = int(os.environ.get("PORT", "8000"))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()


def main() -> None:
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    if not settings.telegram_bot_token:
        print("TELEGRAM_BOT_TOKEN not configured. Skipping bot startup.")
        return

    app = Application.builder().token(settings.telegram_bot_token).build()
    for handler in obtener_handlers():
        app.add_handler(handler)
    print("Bot started. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
