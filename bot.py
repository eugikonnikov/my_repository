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
