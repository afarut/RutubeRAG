import os
from telegram.ext import ApplicationBuilder
from .handlers import register_handlers
from .database import init_db

def main() -> None:
    bot_token = os.getenv('BOT_TOKEN')

    if not bot_token:
        raise ValueError("Не удалось найти переменную окружения BOT_TOKEN")

    init_db()
    
    application = ApplicationBuilder().token(bot_token).build()
    
    register_handlers(application)

    application.run_polling()

if __name__ == '__main__':
    main()
