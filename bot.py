import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram import (
    ReplyKeyboardMarkup,
    Update,
    KeyboardButton,
    ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from telegram.error import NetworkError
import httpx

# --- Логгер ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- Переменные окружения ---
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
MANAGER_IDS = os.getenv("MANAGER_IDS")

# Этапы диалога
(
    POSITION,
    PHONE,
    NAME,
    BRANCH,
    SCHEDULE,
    EXPERIENCE,
    SELFEMPLOYED,
    SALARY_EXPECT,
    VACANCY_INFO,
    FINAL,
) = range(10)



# --- Шаг 1 ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = ReplyKeyboardMarkup(
        [["Сборщик", "Курьер"]], one_time_keyboard=True, resize_keyboard=True
    )
    await update.message.reply_text(
        f"Привет, {user.first_name}!\n"
        "Здесь можно оставить заявку на сборщика или курьера заказов в Boon Express — сервисе экспресс-доставки продуктов в Якутске! 🚀\n\n"
        "Мы ищем энергичных и ответственных людей в нашу команду. Работа рядом с домом, гибкий график и стабильный доход ждут тебя!\n\n"
        "Для начала выбери, пожалуйста, желаемую позицию:",
        reply_markup=keyboard
    )
    return POSITION

# --- Шаг 2 ---
async def position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["position"] = update.message.text
    contact_button = KeyboardButton("📱 Поделиться номером", request_contact=True)
    keyboard = ReplyKeyboardMarkup([[contact_button]], one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "Отлично! Теперь уточни, пожалуйста, свой номер телефона.",
        reply_markup=keyboard
    )
    return PHONE

# --- Шаг 3 ---
async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        context.user_data["phone"] = update.message.contact.phone_number
    else:
        context.user_data["phone"] = update.message.text
    
    await update.message.reply_text(
        "Отлично! Напиши полное имя и возраст.",
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME

# --- Шаг 4 ---
async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    branches = [
        ["203 микрорайон (202-203 мкр)"],
        ["Дзержинского (Дом быта-Крытый рынок)"],
        ["Пояркова (Сахацирк, Городской парк)"],
        ["Залог (к/т Лена, Теплое озеро)"],
        ["Прометей"],
        ["Рыдзинского"],
        ["Ростелеком"],
        ["пл. Дружбы"],
        ["Авиапорт"],
    ]
    await update.message.reply_text(
        "Выбери ближайший или желаемый филиал:",
        reply_markup=ReplyKeyboardMarkup(branches, one_time_keyboard=True, resize_keyboard=True)
    )
    return BRANCH

# --- Шаг 5 ---
async def branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["branch"] = update.message.text
    schedules = [
        ["08:00–16:00"], 
        ["16:00–23:00"], 
        ["08:00–23:00"],
    ]
    await update.message.reply_text(
        "Какой график работы вам удобен?",
        reply_markup=ReplyKeyboardMarkup(schedules, one_time_keyboard=True, resize_keyboard=True)
    )
    return SCHEDULE

# --- Шаг 6 ---
async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["schedule"] = update.message.text
    await update.message.reply_text(
        "Есть ли опыт работы в сборке заказов, на складе или в доставке?",
        reply_markup=ReplyKeyboardMarkup([["Да", "Нет"]], one_time_keyboard=True, resize_keyboard=True)
    )
    return EXPERIENCE

# --- Шаг 7 ---
async def experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["experience"] = update.message.text
    await update.message.reply_text(
        "Готов ли ты оформить статус самозанятого через приложение «Мой налог»?",
        reply_markup=ReplyKeyboardMarkup([["Да", "Нет"]], one_time_keyboard=True, resize_keyboard=True)
    )
    return SELFEMPLOYED

# --- Шаг 8 ---
async def selfemployed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["selfemployed"] = update.message.text
    # Проверяем ответ пользователя
    if update.message.text.lower() == "нет":
        # Завершаем разговор с сообщением о необходимости начать заново
        await update.message.reply_text(
            "Спасибо за ответы! Чтобы работать у нас, необходимо оформить статус самозанятого. "
            "Статус самозанятого можно оформить через приложение «Мой налог».\n\n"
            "Если согласны, заполните анкету заново, нажав /start.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END # Завершаем разговор
    elif update.message.text.lower() == "да":
        # Продолжаем к следующему шагу
        await update.message.reply_text(
            "Какой минимальный доход ты ожидаешь от работы?",
            reply_markup=ReplyKeyboardRemove()
        )
        return SALARY_EXPECT
    else:
        # Если ответ не "Да" или "Нет", просим выбрать из предложенных вариантов
        await update.message.reply_text(
            "Пожалуйста, выбери один из предложенных вариантов: «Да» или «Нет»",
            reply_markup=ReplyKeyboardMarkup([["Да", "Нет"]], one_time_keyboard=True, resize_keyboard=True)
        )
        return SELFEMPLOYED

# --- Шаг 9 ---
async def salary_expect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["salary_expect"] = update.message.text
    position = context.user_data.get("position", "").lower()

    if position == "сборщик":
        await update.message.reply_text(
            "Спасибо за твои ответы! Высылаем подробную информацию.\n\n"
            "📦 Что делает сборщик заказов?\n"
            "• Сборка заказов\n"
            "• Выкладка товаров\n"
            "• Фасовка товаров\n"
            "• Контроль сроков годности\n"
            "• Общение с клиентом\n"
            "• Чистота на складе\n"
            "• Инвентаризация\n"
            "• Взаимодействие со Службой заботы\n"
            "• Прием оплаты\n\n"
            "⚡ Что важно для этой работы?\n"
            "Внимательность, скорость, аккуратность, умение работать в команде, "
            "умение работать в условиях высокой нагрузки. "
            "Знание регламентов сборки и работы на складе.\n\n"
            "📅 График: Формируется еженедельно, согласовывается с супервайзером. "
            "Доступные смены: 08:00–16:00, 16:00–23:00, 08:00–23:00. "
            "Невыход на смену без согласования влечёт удержание из зарплаты.\n\n"
            "💰 Вознаграждение:\n"
            "- Часовая ставка: 220 ₽\n"
            "- За каждый собранный заказ: 10 ₽\n\n"
            "🛠 Стажировка: 10–20 часов, оплачивается по 100 ₽/час.\n\n"
            "💳 Выплаты: еженедельно (пн–ср) на карту при наличии статуса самозанятого "
            "(налог 6% оплачивается самостоятельно).\n\n"
            "📈 Карьерный рост: возможность стать товароведом или управляющим при успешной работе.\n\n"
            "📑 Договор: заключается договор оказания услуг.\n\n"
            "🎓 У нас можно совмещать с учёбой, бесплатно обучаться, мы предоставляем гибкий график. "
            "Чем больше часов, тем выше доход.\n\n"
            "Ты готов присоединиться к нашей команде?\n"
            "Если всё устраивает — поставь + 😊"
        )
    elif position == "курьер":
        await update.message.reply_text(
            "Спасибо за твои ответы! Высылаем подробную информацию.\n\n"
            "🚴 Курьер занимается доставкой заказов: получение, транспортировка, передача.\n\n"
            "⚡ Важно: внимательность, скорость, аккуратность, умение работать в команде "
            "и в условиях высокой нагрузки.\n\n"
            "📅 График: формируется еженедельно, согласовывается с управляющим склада. "
            "Доступные смены: 08:00–16:00, 16:00–23:00, 08:00–23:00. "
            "Невыход на смену без согласования влечёт удержание из зарплаты.\n\n"
            "💰 Вознаграждение:\n"
            "- 1 слой (радиус до 500 м от склада) — 85₽/заказ\n"
            "- 2 слой (радиус до 1000 м от склада) — 100₽/заказ\n\n"
            "🛵 Стажировка: 1 день + инструктаж по эксплуатации электровелосипеда.\n"
            "Электровелосипед выдается в аренду — удержание составляет 13% от вашей недельной зарплаты.\n\n"
            "💳 Выплаты: еженедельно (вт–ср) на карту при наличии статуса самозанятого "
            "(налог 6% оплачивается самостоятельно).\n\n"
            "📈 Карьерный рост: возможность стать товароведом или управляющим при успешной работе.\n\n"
            "📑 Договор: заключается договор оказания услуг.\n\n"
            "🎓 У нас можно совмещать с учёбой, бесплатно обучаться, мы предоставляем гибкий график. "
            "Чем больше часов, тем выше доход.\n\n"
            "Ты готов присоединиться к нашей команде?\n"
            "Если всё устраивает — поставь + 😊"
        )
    return VACANCY_INFO

# --- Шаг 10 ---
async def vacancy_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip() == "+":
        await update.message.reply_text(
            "Спасибо за заявку! Менеджер получит твои ответы и назначит время онлайн-собеседования "
            "в течение 1–2 рабочих дней.\n\n"
            "Онлайн-собеседование пройдет по видеозвонку и займет не более 7 минут.\n"
            "После собеседования можно будет назначить день стажировки, "
            "чтобы выйти на полные смены.\n\n"
            "До скорого! 💜"
        )
        # 2. Сообщение менеджеру
        user_data = context.user_data
        text_to_manager = (
            f"📥 Новая заявка:\n"
            f"Позиция: {user_data.get('position')}\n"
            f"Имя: {user_data.get('name')}\n"
            f"Телефон: {user_data.get('phone')}\n"
            f"Филиал: {user_data.get('branch')}\n"
            f"График: {user_data.get('schedule')}\n"
            f"Опыт: {user_data.get('experience')}\n"
            f"Самозанятый: {user_data.get('selfemployed')}\n"
            f"Доход ожидания: {user_data.get('salary_expect')}"
        )
        for manager_id in MANAGER_IDS:
            try:
                await context.bot.send_message(chat_id=manager_id, text=text_to_manager)
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение менеджеру {manager_id}: {e}")

        return ConversationHandler.END
    else:
        await update.message.reply_text("Поставь +, если согласен.")
        return VACANCY_INFO

# --- Отмена ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог завершён.")
    return ConversationHandler.END

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            POSITION: [MessageHandler(filters.TEXT & ~filters.COMMAND, position)],
            PHONE: [
                MessageHandler(filters.CONTACT, phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, phone),
            ],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            BRANCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, branch)],
            SCHEDULE: [MessageHandler(filters.TEXT & ~filters.COMMAND, schedule)],
            EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, experience)],
            SELFEMPLOYED: [MessageHandler(filters.TEXT & ~filters.COMMAND, selfemployed)],
            SALARY_EXPECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, salary_expect)],
            VACANCY_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, vacancy_info)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    while True:
        try:
            app.run_polling(drop_pending_updates=True)
        except (NetworkError, httpx.ReadError) as e:
            logger.warning(f"Потеряно соединение: {e}. Перезапуск через 5 сек...")
            asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}", exc_info=True)
            break
