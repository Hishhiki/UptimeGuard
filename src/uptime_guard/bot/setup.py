from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from uptime_guard.bot.handlers import start_command, button_handler, handle_text_message
from uptime_guard.config import settings


def setup_bot() -> Application:
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN не задан в .env файле!")

    application = Application.builder().token(settings.telegram_bot_token).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    return application
