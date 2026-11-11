import os
import logging
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)

# Faqat bot egasining Telegram ID raqami
OWNER_ID = 1841808783

# Kanal username'lari
REQUIRED_CHANNELS = [
    ("Jonli Aktiv Obunachi Qo'shish", "@Jonli_Aktiv_Obunachi_Qoshish"),
    ("Jonli Obunachi Qo'shish Aktivuz", "@Jonli_Obunachi_Qoshish_Aktivuz"),
    ("Time Kinolar Uzbek", "@timekinolar_uzbek"),
]

MOVIES_CHANNEL_URL = "https://t.me/Time_Kinolar"
DB_PATH = os.getenv("DB_PATH", "timekinolar_users.db")
UZ_TZ = ZoneInfo("Asia/Tashkent")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def now_uzbekistan():
    return datetime.now(UZ_TZ)


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL
            )
        """)
        conn.commit()


def register_user(user_id: int):
    now = now_uzbekistan().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO users (user_id, first_seen, last_seen)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET last_seen = excluded.last_seen
        """, (user_id, now, now))
        conn.commit()


def get_stats():
    today = now_uzbekistan().date().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]
        today_count = conn.execute(
            "SELECT COUNT(*) FROM users WHERE substr(last_seen, 1, 10) = ?",
            (today,)
        ).fetchone()[0]
    return total, today_count


def subscription_keyboard():
    rows = []
    for index, (title, username) in enumerate(REQUIRED_CHANNELS, start=1):
        url = "https://t.me/" + username.lstrip("@")
        rows.append([InlineKeyboardButton(f"{index} - kanal", url=url)])
    rows.append([InlineKeyboardButton("â Tasdiqlash", callback_data="check_subs")])
    return InlineKeyboardMarkup(rows)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user:
        register_user(update.effective_user.id)

        message = (
            "Assalomu alaykum!\n\n"
            "Botdan foydalanish uchun quyidagi 3 ta kanalga obuna boling.\n"
            "Song Tasdiqlash tugmasini bosing."
        )
    await update.message.reply_text(message, reply_markup=subscription_keyboard())


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or update.effective_user.id != OWNER_ID:
        await update.message.reply_text("â Bu buyruq faqat bot egasi uchun.")
        return

    total, today_count = get_stats()
    await update.message.reply_text(
        "ð TIME KINOLAR BOT STATISTIKASI\n\n"
        f"ð¥ Jami foydalanuvchilar: {total}\n"
        f"ð Bugun kirganlar: {today_count}"
    )


async def check_subscriptions(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    not_joined = []
    for title, username in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=username, user_id=user_id)
            if member.status in ("left", "kicked"):
                not_joined.append(title)
            elif member.status == "restricted" and not getattr(member, "is_member", False):
                not_joined.append(title)
        except Exception:
            logger.exception("Obunani tekshirishda xatolik: %s", username)
            not_joined.append(title)
    return not_joined


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data != "check_subs":
        return

    not_joined = await check_subscriptions(query.from_user.id, context)
    if not_joined:
        await query.edit_message_text(
            "â Hali barcha kanallarga obuna bo'lmagansiz.\n\n"
            "Quyidagi kanallarga obuna bo'ling, keyin yana Â«â TasdiqlashÂ»ni bosing.",
            reply_markup=subscription_keyboard()
        )
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("ð¥ Kinolar kanaliga o'tish", url=MOVIES_CHANNEL_URL)]
    ])
    await query.edit_message_text(
        "â Obuna tasdiqlandi!\n\n"
        "ð¬ Barcha kinolarimiz ushbu kanalda. Marhamat, kanalimizga o'ting!",
        reply_markup=keyboard
    )


def main():
    init_db()
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "BOT_TOKEN topilmadi. Hosting sozlamalarida BOT_TOKEN nomli "
            "environment variable yarating va tokenni uning qiymatiga qo'ying."
        )

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button_handler))
    logger.info("TimeKinolar bot ishga tushmoqda...")
    app.run_polling()


if __name__ == "__main__":
    main()
