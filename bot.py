import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Хранилище данных пользователей и переписок
users = {}
message_replies = {}

# Функция для главного меню
async def show_menu(update: Update):
    menu_keyboard = [
        [KeyboardButton("Список участников"), KeyboardButton("Выбрать адресата")]
    ]
    
    reply_markup = ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Получено сообщение: {update.message.text} от {update.effective_user.id}")
    user_id = update.effective_user.id
    username = update.effective_user.username or f"User_{user_id}"

    if user_id not in users:
        users[user_id] = username
        logger.info(f"Новый пользователь авторизован: {username} (ID: {user_id})")
        await update.message.reply_text("Вы успешно авторизовались в боте!")
    else:
        logger.info(f"Повторная авторизация пользователя: {username} (ID: {user_id})")
        await update.message.reply_text("Вы уже авторизованы!")

    await show_menu(update)

# Команда для отображения списка пользователей
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_list = "\n".join([f"{username} (ID: {uid})" for uid, username in users.items()]) if users else "Пока нет пользователей."
    await update.message.reply_text(f"Список участников:\n{user_list}")

# Команда для выбора пользователя из списка
async def choose_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(users) < 2:
        await update.message.reply_text("Список участников пуст.")
        logger.info(f"Пользователь {user_id} попытался выбрать собеседника, но список пуст.")
        return

    keyboard = [
        [InlineKeyboardButton(username, callback_data=str(target_id))]
        for target_id, username in users.items() if target_id != user_id
    ]

    if keyboard:
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите пользователя для отправки сообщения:", reply_markup=reply_markup)
        logger.info(f"Пользователю {user_id} предложен список собеседников.")
    else:
        await update.message.reply_text("Нет доступных пользователей для отправки сообщений.")
        logger.info(f"Пользователь {user_id} не нашел доступных собеседников.")

# Обработка выбора пользователя из списка
async def handle_user_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    sender_id = query.from_user.id
    receiver_id = int(query.data)

    message_replies[sender_id] = receiver_id

    await query.edit_message_text(
        text=f"Вы выбрали пользователя {users[receiver_id]}! Напишите сообщение для отправки."
    )
    logger.info(f"Пользователь {sender_id} выбрал собеседника {receiver_id}.")

# Обработка текстовых сообщений (кнопки и текст)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text

    # Обработка кнопок (главное меню)
    if message == "Список участников":
        await list_users(update, context)
    elif message == "Выбрать адресата":
        await choose_user(update, context)
    else:
        # Проверяем, выбран ли собеседник
        if user_id not in message_replies:
            await update.message.reply_text("Сначала выберите адресата с помощью кнопки 'Выбрать адресата'.")
            return

        # Отправка сообщения
        receiver_id = message_replies[user_id]
        await context.bot.send_message(
            chat_id=receiver_id,
            text=f"Вам письмо от Тайного Санты: \n{message}\n\nВы можете ответить ему, и бот перенаправит ваш ответ обратно."
        )
        logger.info(f"Сообщение от пользователя {user_id} отправлено пользователю {receiver_id}. Текст: {message}")

        message_replies[receiver_id] = user_id  # Сохраняем информацию для ответов
        await update.message.reply_text("Ваше письмо отправлено!")

# Основная функция
def main():
    # Создаем объект Application
    application = Application.builder().token("7244231240:AAF058JkWuJPYtjIUySSIT3swUE8Dt_u_bE").build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # Обрабатываем и кнопки, и текст
    application.add_handler(CallbackQueryHandler(handle_user_selection))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
