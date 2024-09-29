from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler
from .handlers_functions import (
    start, admin, operator_password_input, handle_message, 
    show_question, accept_bot_answer, write_own_answer, operator_reply, exit_operator
)

def register_handlers(application):
    """Регистрация всех обработчиков в приложении."""
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, operator_password_input))
    application.add_handler(CallbackQueryHandler(show_question, pattern='question_'))
    application.add_handler(CallbackQueryHandler(accept_bot_answer, pattern='accept_bot_answer'))
    application.add_handler(CallbackQueryHandler(write_own_answer, pattern='write_own_answer'))
    application.add_handler(CallbackQueryHandler(exit_operator, pattern='exit_operator'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.REPLY & filters.TEXT, operator_reply))
