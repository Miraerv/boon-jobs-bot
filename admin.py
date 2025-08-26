# admin.py
import os
import ast
import math
import logging
import io
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from db import (
    fetch_applications,
    count_applications,
    get_application,
    delete_application,
    export_applications_csv,
)

load_dotenv()
logger = logging.getLogger(__name__)

# Парсим MANAGER_IDS (как в bot.py). Ожидаем формат env: [12345, 67890]
MANAGER_IDS = []
manager_ids_str = os.getenv("MANAGER_IDS")
if manager_ids_str:
    try:
        MANAGER_IDS = ast.literal_eval(manager_ids_str)
    except Exception:
        logger.exception("Не удалось распарсить MANAGER_IDS")
        MANAGER_IDS = []


def _is_admin(user_id: int) -> bool:
    return user_id in MANAGER_IDS


# ---- Хелпер: отрисовка страницы заявок ----
async def _render_apps_page_text_and_markup(page: int, per_page: int = 5):
    total = count_applications()
    total_pages = max(1, math.ceil(total / per_page))
    if page < 0:
        page = 0
    if page >= total_pages:
        page = total_pages - 1

    apps = fetch_applications(limit=per_page, offset=page * per_page)
    if not apps:
        text = "Заявок пока нет."
        markup = InlineKeyboardMarkup([])
        return text, markup, page, total_pages

    lines = []
    keyboard = []
    for a in apps:
        lines.append(f"#{a['id']} | {a['position']} — {a['name']} | {a['phone']} | {a['created_at']}")
        # отдельная кнопка для просмотра деталей
        keyboard.append([InlineKeyboardButton(f"Просмотр #{a['id']} — {a['name']}", callback_data=f"view:{a['id']}:{page}")])

    text = f"Список заявок — страница {page+1}/{total_pages}\n\n" + "\n".join(lines)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"page:{page-1}"))
    if page + 1 < total_pages:
        nav_buttons.append(InlineKeyboardButton("➡️ Вперёд", callback_data=f"page:{page+1}"))
    nav_buttons.append(InlineKeyboardButton("📥 Экспорт CSV", callback_data="export"))

    keyboard.append(nav_buttons)
    markup = InlineKeyboardMarkup(keyboard)
    return text, markup, page, total_pages


# ---- Команда /apps ----
async def apps_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not _is_admin(user.id):
        await update.message.reply_text("У вас нет прав для просмотра заявок.")
        return

    page = 0
    if context.args:
        try:
            page = int(context.args[0])
        except Exception:
            page = 0

    text, markup, page, _ = await _render_apps_page_text_and_markup(page)
    await update.message.reply_text(text, reply_markup=markup)


# ---- Обработка callback_query (view, del, page, export) ----
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    if not _is_admin(user.id):
        await query.answer("Нет прав", show_alert=True)
        return
    await query.answer()  # acknowledge

    data = query.data or ""

    # --- Просмотр заявки ---
    if data.startswith("view:"):
        parts = data.split(":")
        app_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0
        app = get_application(app_id)
        if not app:
            await query.edit_message_text("Заявка не найдена.")
            return

        text_lines = [
            f"Заявка #{app['id']}",
            f"Позиция: {app['position']}",
            f"Имя: {app['name']}",
            f"Возраст: {app['age']}",
            f"Телефон: {app['phone']}",
            f"Филиал: {app['branch']}",
            f"График: {app['schedule']}",
            f"Опыт: {app['experience']}",
            f"Опыт вождения: {app.get('driving_experience','')}",
            f"Самозанятый: {app.get('selfemployed','')}",
            f"Ожидаемый доход: {app.get('salary_expect','')}",
            f"Создано: {app.get('created_at')}"
        ]
        text = "\n".join(text_lines)

        kb = [
            [InlineKeyboardButton("Удалить заявку", callback_data=f"del:{app_id}:{page}")],
            [InlineKeyboardButton("Назад к списку", callback_data=f"page:{page}")]
        ]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(kb))

    # --- Удаление заявки ---
    elif data.startswith("del:"):
        parts = data.split(":")
        app_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0
        deleted = delete_application(app_id)
        if deleted:
            text, markup, page, _ = await _render_apps_page_text_and_markup(page)
            await query.edit_message_text(text=text, reply_markup=markup)
        else:
            await query.answer("Не удалось удалить заявку.", show_alert=True)

    # --- Навигация по страницам ---
    elif data.startswith("page:"):
        page = int(data.split(":")[1])
        text, markup, page, _ = await _render_apps_page_text_and_markup(page)
        await query.edit_message_text(text=text, reply_markup=markup)

    # --- Первый клик на экспорт: выбор позиции ---
    elif data == "export":
        kb = [
            [InlineKeyboardButton("Все", callback_data="export_all")],
            [InlineKeyboardButton("Сборщики", callback_data="export_Сборщик")],
            [InlineKeyboardButton("Курьеры", callback_data="export_Курьер")]
        ]
        await query.edit_message_text("Выберите позицию для экспорта:", reply_markup=InlineKeyboardMarkup(kb))

    # --- Обработка выбора позиции для экспорта ---
    elif data.startswith("export_"):
        pos = data[len("export_"):]
        if pos.lower() == "all":
            pos = None
        csv_bytes = export_applications_csv(position=pos)
        bio = io.BytesIO(csv_bytes)
        bio.name = f"Заявки_{pos or 'Все'}.csv"
        bio.seek(0)
        await context.bot.send_document(chat_id=query.message.chat_id, document=bio)
        await query.answer("CSV отправлен.")

    else:
        await query.answer()  # нечего делать



# ---- регистрируем хендлеры в приложении ----
def register_admin_handlers(app):
    app.add_handler(CommandHandler("apps", apps_list))
    app.add_handler(CallbackQueryHandler(admin_callback))
