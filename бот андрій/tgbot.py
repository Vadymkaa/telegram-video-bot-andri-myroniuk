from __future__ import annotations
import os
import sqlite3
import logging
from datetime import datetime, timezone, time
from typing import List

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ===================== НАЛАШТУВАННЯ =====================
VIDEO_SOURCES: List[str] = [
    "BAACAgIAAxkBAAIBF2jYWKJ-oU85gIgRpEtI61aH4qaDAAJ-jQACdPzBSpHZRi2F_qMjNgQ",
    "BAACAgIAAxkBAAIBF2jYWKJ-oU85gIgRpEtI61aH4qaDAAJ-jQACdPzBSpHZRi2F_qMjNgQ",
    # додайте ще свої відео
]

DB_PATH = os.environ.get("DB_PATH", "users.db")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8101668293:AAE9nLdtt7f3C7JZ97Nt6j5NcEgBVstTjKI")

# Логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ===================== БАЗА ДАНИХ =====================
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    chat_id INTEGER PRIMARY KEY,
    started_at TEXT NOT NULL,
    last_index INTEGER NOT NULL DEFAULT -1
);
"""

UPSERT_USER_SQL = (
    "INSERT INTO users(chat_id, started_at, last_index) VALUES(?, ?, ?) "
    "ON CONFLICT(chat_id) DO UPDATE SET started_at=excluded.started_at;"
)
UPDATE_LAST_INDEX_SQL = "UPDATE users SET last_index=? WHERE chat_id=?;"
DELETE_USER_SQL = "DELETE FROM users WHERE chat_id=?;"
GET_ALL_USERS_SQL = "SELECT chat_id, started_at, last_index FROM users;"


def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


# ===================== ЛОГІКА ВІДПРАВКИ =====================
async def send_next_video(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Надсилає користувачу 7 відео підряд щодня о 10:01"""
    job = context.job
    chat_id = job.chat_id

    if not VIDEO_SOURCES:
        logger.warning("VIDEO_SOURCES порожній. Нічого надсилати.")
        return

    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT last_index FROM users WHERE chat_id=?;", (chat_id,))
        row = cur.fetchone()
        if row is None:
            job.schedule_removal()
            return

        last_index = row[0]

        # надсилаємо одразу 7 відео
        for i in range(7):
            next_index = (last_index + 1 + i) % len(VIDEO_SOURCES)
            source = VIDEO_SOURCES[next_index]

            await context.bot.send_video(
                chat_id=chat_id,
                video=source,
                caption=f"Відео {next_index + 1} з {len(VIDEO_SOURCES)} 🎬"
            )

        # оновлюємо індекс (останнє надіслане)
        cur.execute(UPDATE_LAST_INDEX_SQL, ((last_index + 7) % len(VIDEO_SOURCES), chat_id))
        conn.commit()
    except Exception:
        logger.exception("Помилка при відправці відео користувачу %s", chat_id)
    finally:
        conn.close()


def schedule_user_job(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    """Запускає щоденну розсилку о 10:01"""
    name = f"daily_video_{chat_id}"
    for j in context.job_queue.get_jobs_by_name(name):
        j.schedule_removal()

    context.job_queue.run_daily(
        send_next_video,
        time=time(10, 1),  # кожного дня о 10:01
        chat_id=chat_id,
        name=name,
    )


# ===================== ХЕНДЛЕРИ =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    conn = get_db_conn()
    with conn:
        conn.execute(
            UPSERT_USER_SQL,
            (chat_id, datetime.now(timezone.utc).isoformat(), -1),
        )
    conn.close()

    # одразу перше відео
    first_video = VIDEO_SOURCES[0]
    await context.bot.send_video(
        chat_id=chat_id,
        video=first_video,
        caption="Перше відео одразу 🎬"
    )

    # ставимо щоденну розсилку
    schedule_user_job(context, chat_id)

    await update.message.reply_text(
        f"Вітаю, {update.effective_user.first_name or 'друже'}! "
        f"Ти отримав перше відео одразу, а далі щодня о 10:01 буде приходити 7 нових."
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    for j in context.job_queue.get_jobs_by_name(f"daily_video_{chat_id}"):
        j.schedule_removal()

    conn = get_db_conn()
    with conn:
        conn.execute(DELETE_USER_SQL, (chat_id,))
    conn.close()

    await update.message.reply_text("Зупинив розсилку й видалив твій прогрес. Повернутись: /start")


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT started_at, last_index FROM users WHERE chat_id=?;", (chat_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        await update.message.reply_text("Ти ще не підписаний. Натисни /start")
        return

    started_at, last_index = row
    total = len(VIDEO_SOURCES)
    sent = max(0, last_index + 1)

    await update.message.reply_text(
        f"Старт: <code>{started_at}</code>\n"
        f"Надіслано: <b>{sent}</b> із <b>{total}</b>\n"
        f"(щодня о 10:01 надсилається 7 відео)",
        parse_mode=ParseMode.HTML,
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Я надсилаю 7 відео щодня о 10:01 після /start.\n\n"
        "Команди:\n/start — підписатися\n/stop — відписатися\n/status — прогрес\n/help — довідка"
    )


async def echo_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.message.video:
        await update.message.reply_text(
            f"Отримав file_id: <code>{update.message.video.file_id}</code>",
            parse_mode=ParseMode.HTML,
        )


# ===================== INIT APP =====================
async def post_init(app: Application) -> None:
    conn = get_db_conn()
    with conn:
        conn.execute(CREATE_TABLE_SQL)
    conn.close()

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(GET_ALL_USERS_SQL)
    rows = cur.fetchall()
    conn.close()

    for chat_id, _, last_index in rows:
        app.job_queue.run_daily(
            send_next_video,
            time=time(10, 1),
            chat_id=chat_id,
            name=f"daily_video_{chat_id}",
        )
        logger.info("Відновив розсилку для chat_id=%s (last_index=%s)", chat_id, last_index)


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("Не задано BOT_TOKEN у змінній середовища!")

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("status", status_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(MessageHandler(filters.VIDEO & filters.ChatType.PRIVATE, echo_video))

    # 🔑 Перед запуском polling видаляємо webhook
    application.bot.delete_webhook(drop_pending_updates=True)

    application.run_polling(close_loop=False)


if __name__ == "__main__":
    main()


