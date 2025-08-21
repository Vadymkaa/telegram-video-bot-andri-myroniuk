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
    "BAACAgIAAxkBAAMDaJ2FmSUaqJHK8QMifzVXlBzVedQAAi59AAKhIelIj65YngFyDuk2BA",
    "BAACAgIAAxkBAAMZaJ2IJY_C-gGkKV5phQnBWEJ2pYoAAkp9AAKhIelI1LisVtq0YbA2BA",
]

DB_PATH = os.environ.get("DB_PATH", "users.db")
BOT_TOKEN = "8101668293:AAE9nLdtt7f3C7JZ97Nt6j5NcEgBVstTjKI"
PORT = int(os.getenv("PORT", 8080))
WEBHOOK_URL = f"https://{os.getenv('RAILWAY_STATIC_URL', '')}/webhook"

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
GET_ALL_USERS_SQL = "SELECT chat_id, started_at, last_index FROM users;"
UPSERT_USER_SQL = """
INSERT INTO users(chat_id, started_at, last_index) VALUES(?, ?, ?)
ON CONFLICT(chat_id) DO UPDATE SET started_at=excluded.started_at;
"""
UPDATE_LAST_INDEX_SQL = "UPDATE users SET last_index=? WHERE chat_id=?;"
DELETE_USER_SQL = "DELETE FROM users WHERE chat_id=?;"

def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

# ===================== ЛОГІКА ВІДПРАВКИ =====================
async def send_next_video(context: ContextTypes.DEFAULT_TYPE) -> None:
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
            logger.info("Користувача %s немає в БД, скасовуємо job.", chat_id)
            job.schedule_removal()
            return
        last_index = row[0]
        next_index = (last_index + 1) % len(VIDEO_SOURCES)

        await context.bot.send_video(chat_id=chat_id, video=VIDEO_SOURCES[next_index])
        cur.execute(UPDATE_LAST_INDEX_SQL, (next_index, chat_id))
        conn.commit()
    except Exception:
        logger.exception("Помилка при відправці відео користувачу %s", chat_id)
    finally:
        conn.close()

def schedule_user_job(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    """Плануємо щоденну відправку о 07:00 ранку."""
    name = f"daily_video_{chat_id}"
    for j in context.job_queue.get_jobs_by_name(name):
        j.schedule_removal()

    context.job_queue.run_daily(
        send_next_video,
        time=time(hour=7, minute=0),
        chat_id=chat_id,
        name=name,
    )

# ===================== ХЕНДЛЕРИ =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id

    # Додаємо або оновлюємо користувача в БД
    conn = get_db_conn()
    with conn:
        conn.execute(
            UPSERT_USER_SQL,
            (chat_id, datetime.now(timezone.utc).isoformat(), -1),
        )
    conn.close()

    # Відправляємо перше відео одразу
    if VIDEO_SOURCES:
        try:
            await context.bot.send_video(chat_id=chat_id, video=VIDEO_SOURCES[0])
            conn = get_db_conn()
            with conn:
                conn.execute(UPDATE_LAST_INDEX_SQL, (0, chat_id))
            conn.close()
        except Exception:
            logger.exception("Помилка при відправці першого відео користувачу %s", chat_id)

    # Наступні відео щодня о 07:00
    schedule_user_job(context, chat_id)

    await update.message.reply_text(
        "Вітаю! Перше відео надіслано, далі щодня о 10:00 буду надсилати наступні."
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    name = f"daily_video_{chat_id}"
    for j in context.job_queue.get_jobs_by_name(name):
        j.schedule_removal()

    conn = get_db_conn()
    with conn:
        conn.execute(DELETE_USER_SQL, (chat_id,))
    conn.close()

    await update.message.reply_text("Розсилку зупинено. Щоб підписатись знову — /start")

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
    remaining = total - sent

    await update.message.reply_text(
        f"Старт: {started_at}\nНадіслано: {sent}/{total}\nЗалишилось: {remaining}",
        parse_mode=ParseMode.HTML
    )

async def echo_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.message.video:
        await update.message.reply_text(
            f"Отримав file_id: <code>{update.message.video.file_id}</code>",
            parse_mode=ParseMode.HTML
        )

# ===================== ІНІЦІАЛІЗАЦІЯ =====================
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

    for chat_id, started_at, last_index in rows:
        app.job_queue.run_daily(
            send_next_video,
            time=time(hour=7, minute=0),
            chat_id=chat_id,
            name=f"daily_video_{chat_id}",
        )

def main():
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("status", status_cmd))
    application.add_handler(MessageHandler(filters.VIDEO & filters.ChatType.PRIVATE, echo_video))

    if os.getenv("RAILWAY_STATIC_URL"):
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="webhook",
            webhook_url=WEBHOOK_URL
        )
    else:
        application.run_polling()

if __name__ == "__main__":
    main()

