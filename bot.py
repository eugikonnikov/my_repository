import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
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
active_chats = {}
message_replies = {}

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

    await update.message.reply_text("Теперь вы можете выбрать пользователя для отправки сообщения.")

# Команда для выбора пользователя из списка
async def choose_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not users:
        await update.message.reply_text("Нет других пользователей для общения.")
        logger.info(f"Пользователь {user_id} попытался выбрать собеседника, но список пуст.")
        return

    keyboard = [
        [InlineKeyboardButton(username, callback_data=str(target_id))]
        for target_id, username in users.items()
        if target_id != user_id
    ]

    if not keyboard:
        await update.message.reply_text("Нет доступных пользователей для отправки сообщений.")
        logger.info(f"Пользователь {user_id} не нашел доступных собеседников.")
        return

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите пользователя для отправки сообщения:", reply_markup=reply_markup)
    logger.info(f"Пользователю {user_id} предложен список собеседников.")

# Обработка выбора пользователя из списка
async def handle_user_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    sender_id = query.from_user.id
    receiver_id = int(query.data)

    active_chats[sender_id] = receiver_id

    await query.edit_message_text(
        text=f"Вы выбрали отправку сообщения пользователю {users[receiver_id]}! Теперь напишите ваше сообщение."
    )
    logger.info(f"Пользователь {sender_id} выбрал собеседника {receiver_id}.")

# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = update.effective_user.id

    if sender_id not in active_chats:
        await update.message.reply_text("Сначала выберите пользователя для общения командой /choose_user.")
        logger.warning(f"Пользователь {sender_id} отправил сообщение без выбора собеседника.")
        return

    receiver_id = active_chats[sender_id]
    message = update.message.text

    # Отправляем сообщение пользователю, с пометкой "от тайного Санты"
    await context.bot.send_message(
        chat_id=receiver_id,
        text=f"Вам письмо от тайного Санты: \n{message}"
    )
    logger.info(f"Сообщение от пользователя {sender_id} отправлено пользователю {receiver_id}. Текст: {message}")

    # Сохраняем ID сообщения, чтобы отслеживать, кто кому ответил
    message_replies[receiver_id] = sender_id  # Получатель становится отправителем в следующем чате
    await update.message.reply_text("Ваше сообщение отправлено!")

# Обработка ответа от пользователя (пересылаем его обратно отправителю)
async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = update.effective_user.id

    # Проверяем, кому нужно отправить ответ
    if sender_id not in message_replies:
        await update.message.reply_text("Никто не ждет ответа от вас.")
        logger.warning(f"Пользователь {sender_id} попытался ответить, но активного чата нет.")
        return

    receiver_id = message_replies[sender_id]
    message = update.message.text

    # Отправляем ответ обратно тому, кто отправил оригинальное сообщение
    await context.bot.send_message(
        chat_id=receiver_id,
        text=f"Ваш подопечный ответил: \n{message}"
    )
    logger.info(f"Ответ от пользователя {sender_id} отправлен пользователю {receiver_id}. Текст: {message}")

    await update.message.reply_text("Ваш ответ отправлен!")

# Команда /list для отображения списка пользователей
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not users:
        await update.message.reply_text("Пока никто не авторизовался.")
        logger.info(f"Пользователь {user_id} запросил список, но он пуст.")
        return

    # Создаем список пользователей
    user_list = "\n".join([f"{username} (ID: {uid})" for uid, username in users.items()])
    await update.message.reply_text(f"Список авторизовавшихся пользователей:\n{user_list}")
    logger.info(f"Пользователь {user_id} запросил список пользователей. Отправлен список: {user_list}")

# Основная функция
def main():
    # Создаем объект Application
    application = Application.builder().token("7244231240:AAF058JkWuJPYtjIUySSIT3swUE8Dt_u_bE").build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("choose_user", choose_user))
    application.add_handler(CommandHandler("list", list_users))  # Добавлен обработчик для /list
    application.add_handler(CallbackQueryHandler(handle_user_selection))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.REPLY & ~filters.COMMAND, handle_reply))

    logger.info("Бот запущен и готов к работе.")
    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
