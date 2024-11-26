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
        [KeyboardButton("🟩 /choose_user")],
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

    if not users or len(users) < 2:
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

    await query.edit_message_text(
        text=f"Вы выбрали пользователя {users[receiver_id]}! Напишите сообщение для отправки."
    )
    logger.info(f"Пользователь {sender_id} выбрал собеседника {receiver_id}.")

# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = update.effective_user.id
    message = update.message.text

    # Проверяем, выбрал ли пользователь адресата
    if sender_id not in message_replies:
        await update.message.reply_text(
            "Сначала выберите адресата с помощью команды /choose_user."
        )
        logger.warning(f"Пользователь {sender_id} отправил сообщение без выбора собеседника.")
        return

    receiver_id = message_replies[sender_id]

    # Отправляем письмо адресату
    await context.bot.send_message(
        chat_id=receiver_id,
        text=f"Вам письмо от Тайного Санты: \n{message}\n\nВы можете ответить ему, и бот перенаправит ваш ответ обратно."
    )
    logger.info(f"Сообщение от пользователя {sender_id} отправлено пользователю {receiver_id}. Текст: {message}")

    # Сохраняем информацию для ответов
    message_replies[receiver_id] = sender_id  # Получатель становится отправителем в следующем чате
    await update.message.reply_text("Ваше письмо отправлено!")

# Обработка ответа от пользователя
async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = update.effective_user.id
    message = update.message.text

    # Проверяем, кому нужно отправить ответ
    if sender_id not in message_replies:
        await update.message.reply_text("Никто не ждет вашего ответа.")
        logger.warning(f"Пользователь {sender_id} попытался ответить, но нет активного письма.")
        return

    receiver_id = message_replies[sender_id]

    # Отправляем ответ обратно отправителю
    await context.bot.send_message(
        chat_id=receiver_id,
        text=f"Вам пришел ответ от Тайного Санты: \n{message}"
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
    application.add_handler(CallbackQueryHandler(handle_user_selection))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.REPLY & ~filters.COMMAND, handle_reply))

    logger.info("Бот запущен и готов к работе.")
    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
