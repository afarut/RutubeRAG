import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

operator_password = os.getenv('OPERATOR_PASSWORD')
operators = {}
pending_questions = []  
waiting_for_password = {}
operator_current_question = {}
api_placeholder_answer = "Здесь будет ответ от API."
operator_reply_state = {}

import aiohttp

async def get_api_answer(question: str) -> str:
    api_url = 'http://176.123.167.46:8080/predict'
    payload = {'question': question}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("answer", "Ошибка: ответ не получен.")
            else:
                return "Ошибка при запросе к API."



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привет! Я интеллектуальный помощник RUTUBE. Ты можешь обратиться ко мне с любым вопросом!")
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    user_id = update.message.from_user.id

    if user_id in operator_reply_state and operator_reply_state[user_id]:
        question_index = operator_current_question[user_id]
        question_user_id, _, _ = pending_questions[question_index]
        await context.bot.send_message(chat_id=question_user_id, text=f"Оператор ответил: {user_message}")

        await update.message.reply_text("Ответ отправлен пользователю.")

        del operator_current_question[user_id]
        pending_questions.pop(question_index)
        operator_reply_state[user_id] = False

        await show_operator_menu(update, context)
    else:
        pending_questions.append((user_id, user_message))
        await update.message.reply_text(f"Ваш вопрос отправлен оператору: {user_message}")
    
        bot_answer = await get_api_answer(user_message)
        
        pending_questions[-1] = (user_id, user_message, bot_answer)

        for operator_id in operators:
            await context.bot.send_message(chat_id=operator_id, text=f"Поступил новый вопрос: {user_message}")





async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    waiting_for_password[update.message.from_user.id] = True
    await update.message.reply_text("Введите пароль для входа как оператор.")

async def operator_password_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id in waiting_for_password:
        user_input = update.message.text
        if user_input == operator_password:
            operators[user_id] = True
            del waiting_for_password[user_id]
            await update.message.reply_text("Вы успешно вошли как оператор.")
            await show_operator_menu(update, context)
        else:
            await update.message.reply_text("Неверный пароль. Попробуйте снова.")
            del waiting_for_password[user_id]
    else:
        await handle_message(update, context)

async def show_operator_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if pending_questions:
        keyboard = [[InlineKeyboardButton(f"Вопрос {i+1}", callback_data=f'question_{i}')] for i in range(len(pending_questions))]
        keyboard.append([InlineKeyboardButton("Выйти", callback_data='exit_operator')])
    else:
        keyboard = [[InlineKeyboardButton("Нет вопросов для обработки", callback_data='no_questions')]]
        keyboard.append([InlineKeyboardButton("Выйти", callback_data='exit_operator')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Выберите вопрос для ответа:", reply_markup=reply_markup)

async def show_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    operator_id = query.from_user.id

    question_index = int(query.data.split('_')[1])
    operator_current_question[operator_id] = question_index

    user_id, question, bot_answer = pending_questions[question_index]

    await query.message.edit_text(f"Вопрос: {question}\nОтвет бота: {bot_answer}")

    keyboard = [
        [InlineKeyboardButton("Принять ответ бота", callback_data='accept_bot_answer')],
        [InlineKeyboardButton("Написать свой ответ", callback_data='write_own_answer')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    await query.answer()



async def accept_bot_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    operator_id = query.from_user.id

    if operator_id in operator_current_question:
        question_index = operator_current_question[operator_id]
        question_user_id, _, bot_answer = pending_questions[question_index]

        await query.message.delete()

        await context.bot.send_message(chat_id=question_user_id, text=f"Оператор принял ответ бота: {bot_answer}")
        
        del operator_current_question[operator_id]
        pending_questions.pop(question_index)

        await query.message.reply_text("Ответ бота отправлен пользователю.")
        
        await show_operator_menu(query, context)
        await query.answer()


async def write_own_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    operator_id = query.from_user.id

    if operator_id in operator_current_question:
        await query.message.delete()

        operator_reply_state[operator_id] = True
        await query.message.reply_text("Введите ваш ответ для пользователя.")
    await query.answer()

async def operator_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    operator_id = update.message.from_user.id

    if operator_id in operator_reply_state and operator_reply_state[operator_id]:
        question_index = operator_current_question.get(operator_id)
        if question_index is not None:
            question_user_id, _ = pending_questions[question_index]

            await context.bot.send_message(chat_id=question_user_id, text=f"Оператор ответил: {update.message.text}")

            await update.message.reply_text("Ответ отправлен пользователю.")

            del operator_current_question[operator_id]
            pending_questions.pop(question_index)

            del operator_reply_state[operator_id]

            await show_operator_menu(update, context)
        else:
            await update.message.reply_text("Вы не выбрали вопрос для ответа.")
    else:
        await update.message.reply_text("Вы не находитесь в режиме оператора или не выбрали вопрос.")


async def exit_operator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.callback_query.from_user.id
    operators.pop(user_id, None)        
    operator_current_question.pop(user_id, None)

    await update.callback_query.answer()

    await update.callback_query.message.delete()

    await update.callback_query.message.reply_text("Вы вышли из режима оператора.")

