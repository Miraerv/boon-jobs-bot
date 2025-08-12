import os
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, Update, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
MANAGER_ID = int(os.getenv("MANAGER_ID"))

# Этапы диалога
(
    PHONE,
    NAME,
    BRANCH,
    SCHEDULE,
    EXPERIENCE,
    SELFEMPLOYED,
    SALARY_EXPECT,
    VACANCY_INFO,
    FINAL,
) = range(9)

# --- Шаг 1 ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Кнопка для запроса контакта
    contact_button = KeyboardButton("📱 Поделиться номером", request_contact=True)
    keyboard = ReplyKeyboardMarkup([[contact_button]], one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        f"Привет, {user.first_name}!\n"
        "Здесь можно узнать подробности на вакансию сборщика заказов в Boon Express 🚀\n\n"
        "Для начала уточни, пожалуйста, свой номер телефона:",
        reply_markup=keyboard
    )
    return PHONE

# --- Шаг 2 ---
async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    context.user_data["phone"] = contact.phone_number
    
    await update.message.reply_text(
        "Отлично, номер для связи получен. Теперь напиши полные фамилию и имя.",
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME

# --- Шаг 3 ---
async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    branches = [
        ["203 микрорайон"],
        ["Дзержинского"],
        ["Пояркова"],
        ["Залог"],
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

# --- Шаг 4 ---
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

# --- Шаг 5 ---
async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["schedule"] = update.message.text
    await update.message.reply_text(
        "Есть ли опыт работы в сборке заказов, на складе или в доставке?",
        reply_markup=ReplyKeyboardMarkup([["Да", "Нет"]], one_time_keyboard=True, resize_keyboard=True)
    )
    return EXPERIENCE

# --- Шаг 6 ---
async def experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["experience"] = update.message.text
    await update.message.reply_text(
        "Готовы ли вы оформить статус самозанятого через приложение «Мой налог»?",
        reply_markup=ReplyKeyboardMarkup([["Да", "Нет"]], one_time_keyboard=True, resize_keyboard=True)
    )
    return SELFEMPLOYED

# --- Шаг 7 ---
async def selfemployed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["selfemployed"] = update.message.text
    
    # Проверяем ответ пользователя
    if update.message.text.lower() == "нет":
        # Создаем кнопку для перезапуска анкеты
        keyboard = [[InlineKeyboardButton("🔄 Заполнить анкету заново", callback_data="restart_form")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Завершаем разговор с информационным сообщением и кнопкой
        await update.message.reply_text(
            "Спасибо за ответы! Чтобы работать у нас, необходимо оформить статус самозанятого. "
            "Статус самозанятого можно оформить через приложение «Мой налог».",
            reply_markup=reply_markup
        )
        return ConversationHandler.END  # Завершаем разговор
        
    elif update.message.text.lower() == "да":
        # Продолжаем к следующему шагу
        await update.message.reply_text(
            "Какой минимальный доход вы ожидаете от работы?",
            reply_markup=ReplyKeyboardRemove()
        )
        return SALARY_EXPECT
        
    else:
        # Если ответ не "Да" или "Нет", просим выбрать из предложенных вариантов
        await update.message.reply_text(
            "Пожалуйста, выберите один из предложенных вариантов: «Да» или «Нет»",
            reply_markup=ReplyKeyboardMarkup([["Да", "Нет"]], one_time_keyboard=True, resize_keyboard=True)
        )
        return SELFEMPLOYED

# --- Шаг 8 ---
async def salary_expect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["salary_expect"] = update.message.text
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
        "Внимательность, скорость, аккуратность, умение работать в команде, умение работать "
        "в условиях высокой нагрузки, знание регламентов сборки и работы на складе.\n\n"
        "📅 График: Формируется еженедельно и согласовывается с супервайзером.\n"
        "Доступные смены: 08:00–16:00, 16:00–23:00, 08:00–23:00.\n"
        "Невыход на смену без согласования — удержание из зарплаты.\n\n"
        "💰 Вознаграждение:\n"
        "• Часовая ставка: 220 ₽\n"
        "• За каждый собранный заказ: 10 ₽\n\n"
        "📝 Стажировка: 10–20 часов, 100 ₽/час\n\n"
        "💳 Выплаты: Еженедельно (понедельник–среда) на карту при наличии статуса самозанятого "
        "(налог 6% оплачивается самостоятельно)\n\n"
        "📈 Карьерный рост: Возможность стать товароведом или управляющим при успешной работе\n\n"
        "📄 Договор: Заключается договор оказания услуг\n\n"
        "🎓 Мы предлагаем: возможность совмещать с учебой, бесплатное обучение, гибкий график. "
        "Чем больше часов, тем выше доход.\n\n"
        "Ты готов присоединиться к нашей команде?\n"
        "Если всё устраивает — поставь + 😊"
    )
    return VACANCY_INFO

# --- Шаг 9 ---
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
            f"Имя: {user_data.get('name')}\n"
            f"Телефон: {user_data.get('phone')}\n"
            f"Филиал: {user_data.get('branch')}\n"
            f"График: {user_data.get('schedule')}\n"
            f"Опыт: {user_data.get('experience')}\n"
            f"Самозанятый: {user_data.get('selfemployed')}\n"
            f"Доход ожидания: {user_data.get('salary_expect')}"
        )
        await context.bot.send_message(chat_id=MANAGER_ID, text=text_to_manager)

        return ConversationHandler.END
    else:
        await update.message.reply_text("Поставь +, если согласен.")
        return VACANCY_INFO

# --- Отмена ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог завершён.")
    return ConversationHandler.END

# --- Перезапуск ---
async def restart_form_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    
    await query.edit_message_text("Начинаем заполнение анкеты заново...")
    
    await query.message.reply_text(
        "Поделитесь своим контактом или введите номер телефона:",
        reply_markup=ReplyKeyboardMarkup(
            [["📞 Поделиться контактом"]], 
            one_time_keyboard=True, 
            resize_keyboard=True,
            request_contact=True
        )
    )
    
    return PHONE

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
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

    restart_callback_handler = CallbackQueryHandler(restart_form_callback, pattern="restart_form")


    app.add_handler(conv_handler)
    app.add_handler(restart_callback_handler)

    app.run_polling()
