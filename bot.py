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
    user_id = update.effective_user.id

    if not users:
        await update.message.reply_text("Пока нет пользователей.")
        return

    user_list = "\n".join([f"{username} (ID: {uid})" for uid, username in users.items()])
    await update.message.reply_text(f"Список участников:\n{user_list}")

# Команда для выбора пользователя из списка
async def choose_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Проверка на наличие других пользователей
    if len(users) < 2:
        await update.message.reply_text("Список участников пуст.")
        logger.info(f"Пользователь {user_id} попытался выбрать собеседника, но список пуст.")
        return

    # Создаем список кнопок для выбора собеседников
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

    # Сохраняем информацию о выбранном собеседнике для последующей отправки сообщений
    message_replies[sender_id] = receiver_id

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
            "Сначала выберите адресата с помощью кнопки 'Выбрать адресата'."
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
        await update.message.reply_t
