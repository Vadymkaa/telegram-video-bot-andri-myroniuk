from __future__ import annotations
import os
import sqlite3
import logging
from datetime import datetime, timezone, time, timedelta
from typing import List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters,
)

# ===================== НАЛАШТУВАННЯ =====================
VIDEO_SOURCES: List[str] = [
    "BAACAgIAAxkBAAMIaNlpPylHKMYZj9MoYA6dWh83VKQAArd8AALpGdBKSyJjl6C4OTY2BA",
    "BAACAgIAAxkBAAMKaNlpu6rlFEbEpZ0gvlr8IhCEBG4AAsR8AALpGdBKG8dSjvSb6zs2BA",
    "BAACAgIAAxkBAAMMaNlqRSFlK2EJnZLZ5PqCqFevI58AAtB8AALpGdBKdF_gAAHRlt5TNgQ",
    "BAACAgIAAxkBAAMOaNlqgMIQXDCMQGlEqiPM0FCp27MAAtV8AALpGdBKG_9JlTB3Xng2BA",
    "BAACAgIAAxkBAAMQaNlqyuOKdAUNmWZPXA8n7Ghsvc0AAt18AALpGdBKqWm7YCaVTDU2BA",
    "BAACAgIAAxkBAAMSaNlrBt0eBjzX3JjxNyjRDSwYeoMAAuV8AALpGdBKcvo-xakimQc2BA",
    "BAACAgIAAxkBAAMUaNlreqvtgzvK40SXJhI_Eybqb7cAAu98AALpGdBKP1_258Gm8N42BA",
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

🎥 Після цього відео зможеш відрізняти тактичні кроки від стратегічних і зменшиш хаос у своєму житті.

<b>А якщо хочеш ще більше цікавих стратегічних прийомів — підписуйся на мій Instagram 👇</b>
""",
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
    "🎯 Сьогодні протягом дня, перш ніж зробити будь-яку дію, постав собі питання:\n«Чи наближає це мене до моєї великої мети?»",
    """🎯 За 10 хвилин сформулюй одну річну ціль за формулою:
[Результат] + [Вимірюється чим] + [Термін] + [Навіщо].
А потім викресли цього тижня все, що не веде до цієї цілі.
Ти відчуєш легкість, коли прибираєш зайве.
І тримай бонус на бонус — ось промокод <b>ACADEMY</b>, який дає знижку 15% на усі набори <a href="https://mudri.org">MUDRI</a> до кінця інтенсиву""",
    """🎯 Візьми одну актуальну проблему (робочу чи особисту) і розділи її на два списки: факти та інтерпретації.
Ти здивуєшся, скільки стресу й емоцій виникає лише через припущення, а не через реальність.
""",
    """🎯 Обери одну подію на найближчий місяць і пропиши 3 сценарії:
А — все піде як треба.
B — можуть бути «обмеження»
C — все пішло по одному місцю…нехорошому такому
Уже 10–15 хв цієї вправи зроблять тебе готовим до будь-якого варіанту
""",
    """🎯 Згадай ситуацію, яка зараз «тягне енергію» і не рухається.
Використай «правило трьох сигналів»: якщо сигнал повторився 3 рази або з 3 різних джерел — зміни підхід.
Обери нову дію замість старої.
""",
    """🎯 Візьми одну подію за останній тиждень і зроби метод Stop–Start–Continue:
Stop — що припиняю робити.
Start — що починаю.
Continue — що продовжую.
Це займе 5 хвилин, але дасть готовий план покращення вже на завтра.
""",
    """🎯 Згадай ситуацію, де на тебе тиснули терміновістю, виною чи «усі так роблять».
Сьогодні потренуйся брати паузу хоча б на 3 хвилини перед відповіддю.
Це дозволить зрозуміти, чи рішення справді твоє, чи його нав’язують.
І тримай закляття проти дурні 
""",
]

EXTRA_FILES = {
    2: {
        "file_id": "BQACAgIAAxkBAAMWaNlrlhmIMxyw83LziEfWwjhElE0AAvV8AALpGdBKtgyt93qRCbA2BA",
        "caption": "📄 А ще, як і обіцяв лови файл, який допоможе тобі поставити ціль та зробити хороший план 🚀"
    },
    4: {
        "file_id": "BQACAgIAAxkBAAMYaNlrtQABjOzo9ZfJkpx6ELmPGMsBAAL5fAAC6RnQSpLVoM23a5PnNgQ",
        "caption": "📄 А ще додаю тобі файлик, який допоможе бути спокійним у будь-якій ситуації ✅"
    },
    7: {
        "file_id": "BQACAgIAAxkBAAIBbGjmyqrO2OSWWd8_JpDWOscuc9UaAAKWkQACUwo5S4ink2cSfZEvNgQ",
        "caption": "📄 І тримай закляття проти дурні 💪"
    }
}

DB_PATH = os.environ.get("DB_PATH", "users.db")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7416498608:AAF_uTo0H3Obrr9eTfnJB9Zdd2KrChDFIjA")

# ==== ДОДАНО: пароль для /count та state розмови ====
ADMIN_PASS = os.environ.get("ADMIN_PASS", "22042004")
COUNT_ASK_PWD = 1

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ===================== SQL =====================
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


# ===================== ХЕЛПЕР: захищене відео =====================
async def send_protected_video(context: ContextTypes.DEFAULT_TYPE, chat_id: int, source: str, caption: str | None = None):
    """Надсилає відео з блокуванням пересилання/збереження (офіційні клієнти)."""
    await context.bot.send_video(
        chat_id=chat_id,
        video=source,
        caption=caption,
        parse_mode=ParseMode.HTML,
        protect_content=True,
        supports_streaming=True
    )


# ===================== ЛОГІКА ВІДПРАВКИ =====================
async def send_video_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id

    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT last_index FROM users WHERE chat_id=?", (chat_id,))
        row = cur.fetchone()
        if not row:
            job.schedule_removal()
            return

        last_index = row[0]
        next_index = last_index + 1

    if next_index >= len(VIDEO_SOURCES):
        # Користувач пройшов усі 7 відео
        if last_index >= len(VIDEO_SOURCES):
            job.schedule_removal()
            return

        conn = get_db_conn()
        with conn:
            conn.execute(UPDATE_LAST_INDEX_SQL, (next_index, chat_id))
        conn.close()

        await send_day8_text(context, chat_id)

        job.schedule_removal()
        return

        if next_index < len(BEFORE_TEXTS):
            await context.bot.send_message(
                chat_id=chat_id,
                text=BEFORE_TEXTS[next_index],
                parse_mode=ParseMode.HTML
            )

        await send_protected_video(
            context,
            chat_id,
            VIDEO_SOURCES[next_index],
            caption=f"🎬 Відео {next_index + 1} з {len(VIDEO_SOURCES)}"
        )

        cur.execute(UPDATE_LAST_INDEX_SQL, (next_index, chat_id))
        conn.commit()

        context.job_queue.run_daily(
            send_after_text_job,
            time=time(7, 20),
            chat_id=chat_id,
            name=f"after_text_{chat_id}"
        )

    except Exception:
        logger.exception("Помилка при відправці відео користувачу %s", chat_id)
    finally:
        conn.close()


async def send_after_text_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id

    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT last_index FROM users WHERE chat_id=?", (chat_id,))
        row = cur.fetchone()
        if not row:
            job.schedule_removal()
            return

        # --- початок оригінальної логіки ---
        last_index = row[0]
        day_num = last_index + 1

        if last_index < len(AFTER_TEXTS):
            await context.bot.send_message(
                chat_id=chat_id,
                text=AFTER_TEXTS[last_index],
                parse_mode=ParseMode.HTML
            )

        if last_index == 6:
            context.job_queue.run_daily(
                send_day8_text,
                time=time(7, 1),
                chat_id=chat_id,
                name=f"day8_text_{chat_id}"
            )

        if day_num in EXTRA_FILES:
            extra = EXTRA_FILES[day_num]
            await context.bot.send_document(chat_id=chat_id, document=extra["file_id"], caption=extra["caption"])

        job.schedule_removal()
        # --- кінець оригінальної логіки ---

    except Exception:
        logger.exception("Помилка при відправці after_text %s", chat_id)
    finally:
        conn.close()


async def send_day8_text(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id

    day8_text = """Ну що, вітаю, ти пройшов 7 днів інтенсиву «Стратегічне мислення у житті»!

За цей час ти:
✔ Навчився бачити різницю між тактичними діями і стратегічними кроками.
✔ Сформулював свою «Північну зірку» і прибрав зайве.
✔ Відрізняєш факти від інтерпретацій і приймаєш спокійніші рішення.
✔ Навчився планувати сценарії й бути готовим до несподіванок.
✔ Побачив, як важливо гнучко міняти підхід.
✔ Освоїв техніку навчання з досвіду Stop–Start–Continue.
✔ Розпізнаєш пастки й маніпуляції та тримаєш контроль над власними рішеннями.

Це лише початок. Стратегічне мислення — це не талант, а навичка, яку можна розвивати щодня.
І тепер у тебе є інструменти, щоб застосовувати її у кар’єрі, фінансах, стосунках і будь-яких життєвих виборах.

🚀 Пам’ятай: кожне твоє рішення може бути випадковим або стратегічним. Обирай друге 😉

А ще маєш подарунок від мене – промокод ACADEMY, який дає знижку 15% на усі набори MUDRI <a href="https://mudri.org">mudri.org</a>

Дякую, що пройшов цей шлях зі мною!
— Андрій Миронюк"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Підпишись на інсту 🎯", url="https://www.instagram.com/a_myroniuk/")]
    ])
    await context.bot.send_message(
        chat_id=chat_id,
        text=day8_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


# ===================== ХЕНДЛЕР start =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    conn = get_db_conn()
    with conn:
        conn.execute(UPSERT_USER_SQL, (chat_id, datetime.now(timezone.utc).isoformat(), -1))
    conn.close()

    first_index = 0
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Підпишись на інсту 🎯", url="https://www.instagram.com/a_myroniuk/")]
    ])

    await context.bot.send_video(
        chat_id=chat_id,
        video=VIDEO_SOURCES[first_index],
        caption=BEFORE_TEXTS[first_index],
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
        protect_content=True,
        supports_streaming=True
    )

    conn = get_db_conn()
    with conn:
        conn.execute(UPDATE_LAST_INDEX_SQL, (first_index, chat_id))
    conn.close()

    context.job_queue.run_once(
        send_after_text_job,
        when=15 * 60,
        chat_id=chat_id,
        name=f"after_text_{chat_id}_first"
    )

    schedule_user_job(context, chat_id)


def schedule_user_job(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    for j in context.job_queue.get_jobs_by_name(f"daily_video_{chat_id}"):
        j.schedule_removal()

    context.job_queue.run_daily(
        send_video_job,
        time=time(7, 1),
        chat_id=chat_id,
        name=f"daily_video_{chat_id}"
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    for j in context.job_queue.get_jobs_by_name(f"daily_video_{chat_id}"):
        j.schedule_removal()

    conn = get_db_conn()
    with conn:
        conn.execute(DELETE_USER_SQL, (chat_id,))
    conn.close()

    await update.message.reply_text("🛑 Розсилка зупинена та прогрес видалено.")


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT started_at, last_index FROM users WHERE chat_id=?", (chat_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        await update.message.reply_text("ℹ️ Ти ще не підписаний. Натисни /start")
        return

    started_at, last_index = row
    total = len(VIDEO_SOURCES)
    sent = max(0, last_index + 1)

    await update.message.reply_text(
        f"📅 Старт: <code>{started_at}</code>\n📦 Надіслано: <b>{sent}</b> із <b>{total}</b>",
        parse_mode=ParseMode.HTML
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Я надсилаю відео щодня о 07:01.\n\n"
        "📌 Команди:\n/start — підписатися\n/stop — відписатися\n/status — переглянути прогрес\n/help — довідка"
    )


async def echo_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.video:
        await update.message.reply_text(
            f"🎥 video file_id: <code>{update.message.video.file_id}</code>",
            parse_mode=ParseMode.HTML
        )
    elif update.message.document:
        await update.message.reply_text(
            f"📂 document file_id: <code>{update.message.document.file_id}</code>",
            parse_mode=ParseMode.HTML
        )


# ===================== ДОДАНО: /count з паролем =====================
async def count_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # тільки у приватному чаті
    if update.effective_chat.type != "private":
        await update.message.reply_text("🔒 Команда доступна лише у приватному чаті з ботом.")
        return ConversationHandler.END

    await update.message.reply_text("🔐 Введи пароль:")
    context.user_data["count_attempts"] = 0
    return COUNT_ASK_PWD


async def count_check_pwd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pwd = (update.message.text or "").strip()
    if pwd != ADMIN_PASS:
        attempts = context.user_data.get("count_attempts", 0) + 1
        context.user_data["count_attempts"] = attempts
        if attempts >= 3:
            await update.message.reply_text("⛔️ Невірний пароль. Доступ заборонено.")
            return ConversationHandler.END
        await update.message.reply_text("❌ Невірний пароль. Спробуй ще раз:")
        return COUNT_ASK_PWD

    # пароль ОК — рахуємо користувачів
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users;")
    total = cur.fetchone()[0]
    conn.close()

    await update.message.reply_text(
        f"👥 Користувачів у боті: <b>{total}</b>",
        parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END


async def count_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Скасовано.")
    return ConversationHandler.END


# ===================== INIT APP =====================
async def post_init(app: Application):
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
        if last_index < len(VIDEO_SOURCES):
            app.job_queue.run_daily(send_video_job, time=time(7, 1), chat_id=chat_id, name=f"daily_video_{chat_id}")
            logger.info("Відновив розсилку для chat_id=%s (last_index=%s)", chat_id, last_index)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("Не задано BOT_TOKEN у змінній середовища!")

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("help", help_cmd))

    # === ДОДАНО: /count як розмова з паролем ===
    count_conv = ConversationHandler(
        entry_points=[CommandHandler("count", count_cmd)],
        states={
            COUNT_ASK_PWD: [MessageHandler(filters.TEXT & ~filters.COMMAND, count_check_pwd)],
        },
        fallbacks=[CommandHandler("cancel", count_cancel)],
        name="count_conv",
        persistent=False,
    )
    app.add_handler(count_conv)

    app.add_handler(MessageHandler((filters.VIDEO | filters.Document.ALL) & filters.ChatType.PRIVATE, echo_file))

    app.run_polling()


if __name__ == "__main__":
    main()


