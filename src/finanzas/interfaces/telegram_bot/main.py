from telegram.ext import Application

from finanzas.config.settings import settings
from finanzas.interfaces.telegram_bot.handlers import obtener_handlers


def main() -> None:
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
