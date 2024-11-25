import logging
import random
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import re

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Пул фраз
PHRASES = [
    "Я думаю все будет нормально",
    "С-с-с-с-сука",
    "Ну я не виноват, что вы 5х2 работаете",
    "Не, я сегодня в ночь",
    "Я завтра с утра в гараж",
    "Бля, я весь день проспал",
    "Мож по пейсят?",
    "Бля, включи Боевой скуф",
    "Да чем я вас заебал?",
    "Так, подожди. Я ниче не понял",
    "Ну сорян, по времени мы не договаривались",
    "Бля, сегодня до мастера доебался",
    "Щас бы пивка",
    "Когда в теннис пойдем?",
    "Хочу дачу в Рыбачьем купить",
    "Можно я доебусь?" 
]

# Последовательность смен
SHIFT_SEQUENCE = [
    "1ая дневная",
    "2ая дневная",
    "Выходной, перед ночными",
    "1ая ночная",
    "2ая ночная",
    "Отсыпной",
    "Выходной",
    "Выходной, перед дневными"
]

# Начальная дата и смена
START_DATE = datetime(2023, 8, 1)
START_SHIFT_INDEX = 4  # "2ая ночная"

def get_shift_for_date(date: datetime) -> str:
    delta_days = (date - START_DATE).days
    shift_index = (START_SHIFT_INDEX + delta_days) % len(SHIFT_SEQUENCE)
    return SHIFT_SEQUENCE[shift_index]

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Команда /start получена")
    await update.message.reply_text('Привет! Я бот Денис. Подменяю нашего Дениса, пока он на смене')

# Проверка графика работы
async def check_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    text = update.message.text.lower()
    mention = f"@{context.bot.username.lower()}"  # Формат упоминания бота
    
    if mention in text:
        # Проверяем, если сообщение содержит запрос о графике работы
        match = re.search(r'как ты работаешь (\d{2})\.(\d{2})(?:\.(\d{4}))?', text)
        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            year_str = match.group(3)
            
            if year_str:
                year = int(year_str)
            else:
                year = datetime.now().year
            
            try:
                # Формируем строку даты в формате для strptime
                date_str = f"{year}-{month:02d}-{day:02d}"
                date = datetime.strptime(date_str, "%Y-%m-%d")
                schedule = get_shift_for_date(date)
                # Формируем ответ в формате ДД.ММ
                formatted_date = f"{day:02d}.{month:02d}"
                await update.message.reply_text(f"{formatted_date} {year} у меня {schedule}")
                return True
            except ValueError as e:
                logger.error(f"Ошибка при парсинге даты: {e}")
                await update.message.reply_text("Неправильный формат даты.")
                return True
    return False

# Обработчик сообщений
async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.lower()
    mention = f"@{context.bot.username.lower()}"  # Формат упоминания бота
    
    # Сначала проверяем, если сообщение связано с графиком работы
    if await check_schedule(update, context):
        return

    if mention in text:
        response = random.choice(PHRASES)
    elif text.endswith("да") or text.endswith("да!") or text.endswith("Да"):
        response = "ПИЗДА!"
    elif text.endswith("когда хонду сделаешь?"):
        response = "Какая хонда? Я скоро на мазде гонять буду"
    else:
        return  # Не отвечаем, если нет упоминания и не заканчивается на "да"
    
    logger.info("Ответ на сообщение: %s", response)
    await update.message.reply_text(response)

# Основная функция
async def main() -> None:
    # Токен вашего бота
    token = '7244231240:AAF058JkWuJPYtjIUySSIT3swUE8Dt_u_bE'

    # Создаем приложение и передаем ему токен вашего бота
    application = ApplicationBuilder().token(token).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond))

    # Инициализируем и запускаем бота
    await application.initialize()
    await application.start()
    logger.info("Бот запущен. Нажмите Ctrl+C для завершения.")
    await application.updater.start_polling()
    
    # Держим приложение в рабочем состоянии
    try:
        await asyncio.Future()  # Блокирует выполнение, пока не будет остановлено вручную
    except asyncio.CancelledError:
        pass
    finally:
        await application.updater.stop()
        await application.shutdown()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if str(e) == "This event loop is already running":
            logger.warning("Already running event loop detected. Using current event loop.")
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
        else:
            raise

