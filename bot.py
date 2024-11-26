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
active_chats = {}
message_replies = {}

# Функция для главного меню
async def show_menu(update: Update):
    menu_keyboard = [
        [KeyboardButton("/list"), KeyboardButton("/choose_user")],
        [KeyboardButton("/close")],
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

# Команда для выбора пользователя из списка
async def choose_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in active_chats:
        receiver_id = active_chats[user_id]
        await update.message.reply_text(
            f"Вы уже связаны с пользователем {users[receiver_id]}. Продолжайте общение!"
        )
        return

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

    # Устанавливаем связь между пользователями
    active_chats[sender_id] = receiver_id
    active_chats[receiver_id] = sender_id  # Двусторонний чат

    await query.edit_message_text(
        text=f"Вы выбрали пользователя {users[receiver_id]} для общения! Теперь напишите ваше сообщение."
    )
    logger.info(f"Создан анонимный чат: {sender_id} ↔ {receiver_id}.")

# Команда /list для просмотра списка пользователей
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not users:
        await update.message.reply_text("Список пользователей пуст.")
        logger.info("Команда /list вызвана, но список пользователей пуст.")
        return

    user_list = "\n".join(f"{username} (ID: {user_id})" for user_id, username in users.items())
    await update.message.reply_text(f"Список пользователей:\n{user_list}")
    logger.info("Список пользователей отправлен.")

# Команда /close для закрытия чата
async def close_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        active_chats.pop(partner_id, None)  # Удаляем связь у партнера
        await update.message.reply_text("Чат закрыт. Вы вернулись в главное меню.")
        logger.info(f"Пользователь {user_id} закрыл чат с пользователем {partner_id}.")
    else:
        await update.message.reply_text("У вас нет активного чата.")

    await show_menu(update)

# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = update.effective_user.id
    message = update.message.text

    if sender_id not in active_chats:
        await update.message.reply_text(
            "Вы еще не выбрали получателя. Сначала выберите пользователя для общения командой /choose_user."
        )
        logger.warning(f"Пользователь {sender_id} отправил сообщение без выбора собеседника.")
        return

    receiver_id = active_chats[sender_id]

    # Отправляем сообщение получателю
    await context.bot.send_message(
        chat_id=receiver_id,
        text=f"Вам письмо от тайного Санты: \n{message}"
    )
    logger.info(f"Сообщение от пользователя {sender_id} отправлено пользователю {receiver_id}. Текст: {message}")

    # Сохраняем ID сообщения, чтобы отслеживать, кто кому ответил
    message_replies[receiver_id] = sender_id
    await update.message.reply_text("Ваше сообщение отправлено!")

# Обработка ответа от пользователя
async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = update.effective_user.id

    if sender_id not in message_replies:
        await update.message.reply_text("Никто не ждет ответа от вас.")
        logger.warning(f"Пользователь {sender_id} попытался ответить, но активного чата нет.")
        return

    receiver_id = message_replies[sender_id]
    message = update.message.text

    # Отправляем ответ обратно отправителю
    await context.bot.send_message(
        chat_id=receiver_id,
        text=f"Ваш подопечный ответил: \n{message}"
    )
    logger.info(f"Ответ от пользователя {sender_id} отправлен пользователю {receiver_id}. Текст: {message}")

    await update.message.reply_text("Ваш ответ отправлен!")

# Основная функция
def main():
    # Создаем объект Application
    application = Application.builder().token("7244231240:AAF058JkWuJPYtjIUySSIT3swUE8Dt_u_bE").build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("choose_user", choose_user))
    application.add_handler(CommandHandler("list", list_users))
    application.add_handler(CommandHandler("close", close_chat))
    application.add_handler(CallbackQueryHandler(handle_user_selection))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.REPLY & ~filters.COMMAND, handle_reply))

    logger.info("Бот запущен и готов к работе.")
    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
