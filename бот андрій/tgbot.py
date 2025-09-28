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
    "BAACAgIAAxkBAAIBHGjY7MU7QUdNqNq8YXHRQvF1qTdaAAJ0fAACdPzJSjvFOkJUgG-jNgQ",
    "BAACAgIAAxkBAAIBHmjY7X5x7Tn5ZI47zyesssApwvzlAAJ_fAACdPzJSm2g2qazpe6nNgQ",
    "BAACAgIAAxkBAAIBIGjY7dEa57kfOApIqY7hIVHWoTYqAAKGfAACdPzJSjDlsMLlL9dKNgQ",
    "BAACAgIAAxkBAAIBImjY7mvAOB4qIhRUwtkQ_F_INtwqAAKRfAACdPzJSh-ZC15_tjVaNgQ",
    "BAACAgIAAxkBAAIBJGjY7qck92dkxlpuupFJSpKQfoA-AAKYfAACdPzJSpjYl5gUKA7_NgQ",
    "BAACAgIAAxkBAAIBJmjY7uc5yRSnRoOfL6mVqO5TmtrrAAKbfAACdPzJSvDN7ArHL0OINgQ",
]

BEFORE_TEXTS: List[str] = [
    """Привіт 👋
Вітаю тебе на інтенсиві «Стратегічне мислення у житті»!

Мене звати Андрій Миронюк і цю 7-денну подорож ми пройдемо разом. План такий: щоранку ти отримуватимеш коротке відео та швидкий практичний прийом (Quick Win). Інколи будуть додаткові матеріали.

Головна мета – навчитися мислити стратегічно не лише у бізнесі, а й у щоденному житті: у стосунках, кар’єрі, фінансах чи здоров’ї.

Тому налаштуйся на експеримент: 7 днів уважності, кращих рішень і більшого контролю над власним життям.

Тому стартуємо 🚀
❓Чому одні постійно «гасять пожежі», а інші встигають будувати життя, яке хочуть?
У цьому уроці ти дізнаєшся, що таке стратегічне мислення і як воно допомагає навести порядок у кар’єрі, фінансах, стосунках та здоров’ї.

🎥 Після цього відео зможеш відрізняти тактичні кроки від стратегічних і зменшиш хаос у своєму житті.""",
    """Привіт! Це другий день інтенсиву «Стратегічне мислення у житті».

Без чіткого бачення ми легко відволікаємось на чужі завдання й витрачаємо енергію дарма.
У цьому уроці ти навчишся формулювати власну «Північну зірку» — мету, яка буде орієнтиром на рік і допоможе відрізнити важливе від зайвого.

🎥 Після цього відео ти отримаєш формулу для постановки цілей, які реально мотивують і ведуть уперед.""",
    """Привіт! Це вже третій день інтенсиву.

Ми часто плутаємо факти з припущеннями — і приймаємо рішення «на емоціях». Це створює стрес і плутає реальність.
У цьому уроці ти навчишся розділяти факти й інтерпретації, перевіряти джерела та бачити картину чіткіше.

🎥 Після цього відео ти отримаєш інструмент, який допоможе спокійніше реагувати на події й приймати рішення, що базуються на реальності, а не на здогадках.""",
    """Привіт! Сьогодні четвертий день інтенсиву.

Світ постійно змінюється — і план «А» рідко спрацьовує.
У цьому уроці ти навчишся планувати наперед і створювати кілька сценаріїв розвитку подій. Це допоможе не панікувати, коли щось піде не так.

🎥 Після цього відео ти отримаєш техніку, яка дає внутрішній спокій та відчуття контролю над ситуаціями.""",
    """Привіт! Це вже п’ятий день 🚀

Ми часто чіпляємось за старі плани, навіть коли вони більше не працюють.
У цьому уроці ти дізнаєшся, як вчасно зрозуміти, що пора міняти підхід, і як не витрачати сили на безрезультатні дії.

🎥 Після цього відео ти отримаєш інструмент, який дозволяє бачити сигнали і швидше переключатися на нові рішення.""",
    """Привіт! День шостий, і він про головне джерело росту — твій досвід.

Більшість людей повторює одні й ті ж помилки, бо не робить висновків.
У цьому уроці ти отримаєш просту техніку, яка дозволяє перетворювати будь-який досвід — і успіх, і провал — у практичні уроки.

🎥 Після цього відео ти зрозумієш, як постійно ставати сильнішим і не наступати на ті самі граблі.""",
    """Привіт! Ми на фініші 🎉 Це сьомий день інтенсиву.

Часто ми приймаємо рішення не свої — а нав’язані страхом, терміновістю чи тиском з боку інших.
У цьому уроці ти навчишся бачити ці пастки та брати паузу, щоб зберегти ясність.

🎥 Після цього відео ти зможеш захищати себе від маніпуляцій і приймати рішення, які справді твої.""",
]

AFTER_TEXTS: List[str] = [
    """🎯 Сьогодні протягом дня, перш ніж зробити будь-яку дію, постав собі питання:
«Чи наближає це мене до моєї великої мети?»""",
    """🎯 За 10 хвилин сформулюй одну річну ціль за формулою:
[Результат] + [Вимірюється чим] + [Термін] + [Навіщо].""",
    """🎯 Візьми одну актуальну проблему (робочу чи особисту) і розділи її на два списки: факти та інтерпретації.""",
    """🎯 Обери одну подію на найближчий місяць і пропиши 3 сценарії: A, B, C.""",
    """🎯 Згадай ситуацію, яка зараз «тягне енергію» і не рухається. Використай «правило трьох сигналів».""",
    """🎯 Візьми одну подію за останній тиждень і зроби метод Stop–Start–Continue.""",
    """🎯 Сьогодні потренуйся брати паузу хоча б на 3 хвилини перед відповіддю. Це дозволить зрозуміти, чи рішення справді твоє, чи його нав’язують.""",
]

EXTRA_FILES = {
    2: {"file_id": "📎_ТВОЙ_FILE_ID_ДЛЯ_ДНЯ_2", "caption": "📄 Обіцяний файл до другого дня 🚀"},
    4: {"file_id": "📎_ТВОЙ_FILE_ID_ДЛЯ_ДНЯ_4", "caption": "📄 Додатковий файл для четвертого дня ✅"}
}

DB_PATH = os.environ.get("DB_PATH", "users.db")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8101668293:AAE9nLdtt7f3C7JZ97Nt6j5NcEgBVstTjKI")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

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
    job = context.job
    chat_id = job.chat_id

    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT last_index FROM users WHERE chat_id=?;", (chat_id,))
        row = cur.fetchone()
        if not row:
            job.schedule_removal()
            return

        last_index = row[0]
        next_index = last_index + 1

        # Фінальний 8-й день
        if next_index >= 8:
            final_text = "Привіт! 🎉 Ми дійшли до фінального дня інтенсиву. Дякую, що пройшов цей шлях разом!"
            final_video = "ВАШ_ФІНАЛЬНИЙ_VIDEO_FILE_ID"
            await context.bot.send_message(chat_id=chat_id, text=final_text)
            await context.bot.send_video(chat_id=chat_id, video=final_video, caption="Фінальне відео 🎬")
            job.schedule_removal()
            cur.execute(UPDATE_LAST_INDEX_SQL, (next_index, chat_id))
            conn.commit()
            return

        # Перед відео
        if next_index < len(BEFORE_TEXTS):
            await context.bot.send_message(chat_id=chat_id, text=BEFORE_TEXTS[next_index])

        # Відео
        source = VIDEO_SOURCES[next_index % len(VIDEO_SOURCES)]
        await context.bot.send_video(
            chat_id=chat_id, video=source, caption=f"🎬 Відео {next_index + 1} з 7"
        )

        # Після відео
        if next_index < len(AFTER_TEXTS):
            await context.bot.send_message(chat_id=chat_id, text=AFTER_TEXTS[next_index])

        # Додаткові файли
        day_num = next_index + 1
        if day_num in EXTRA_FILES:
            extra = EXTRA_FILES[day_num]
            await context.bot.send_document(chat_id=chat_id, document=extra["file_id"], caption=extra["caption"])

        cur.execute(UPDATE_LAST_INDEX_SQL, (next_index, chat_id))
        conn.commit()

    except Exception:
        logger.exception("Помилка при відправці відео користувачу %s", chat_id)
    finally:
        conn.close()


def schedule_user_job(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    name = f"daily_video_{chat_id}"
    for j in context.job_queue.get_jobs_by_name(name):
        j.schedule_removal()

    context.job_queue.run_daily(
        send_next_video,
        time=time(10, 1),
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

    # Перше відео одразу
    first_video = VIDEO_SOURCES[0]
    await context.bot.send_video(
        chat_id=chat_id,
        video=first_video,
        caption=BEFORE_TEXTS[0]
    )

    schedule_user_job(context, chat_id)

    await update.message.reply_text(
        f"Ти отримав перше відео одразу, а далі щодня о 10:01 буде приходити нове."
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
        f"(щодня о 10:01 надсилається відео з текстами)",
        parse_mode=ParseMode.HTML,
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Я надсилаю відео щодня о 10:01 після /start.\n\n"
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
        if last_index < 8:
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

    application.bot.delete_webhook(drop_pending_updates=True)
    application.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
