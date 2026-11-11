import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)

# Kanal username'lari (@ belgisisiz)
REQUIRED_CHANNELS = [
    ("Jonli Aktiv Obunachi Qo'shish", "@Jonli_Aktiv_Obunachi_Qoshish"),
    ("Jonli Obunachi Qo'shish Aktivuz", "@Jonli_Obunachi_Qoshish_Aktivuz"),
    ("Time Kinolar Uzbek", "@timekinolar_uzbek"),
]

MOVIES_CHANNEL_URL = "https://t.me/Time_Kinolar"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def subscription_keyboard():
    rows = []
    for index, (title, username) in enumerate(REQUIRED_CHANNELS, start=1):
        url = "https://t.me/" + username.lstrip("@")
        rows.append([InlineKeyboardButton(f"{index} - kanal", url=url)])
    rows.append([InlineKeyboardButton("✅ Tasdiqlash", callback_data="check_subs")])
    return InlineKeyboardMarkup(rows)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "🎬 Assalomu alaykum!\n\n"
        "Botdan foydalanish uchun quyidagi 3 ta kanalga obuna bo'ling.\n"
        "So'ng «✅ Tasdiqlash» tugmasini bosing."
    )
    await update.message.reply_text(message, reply_markup=subscription_keyboard())


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
            # Xatolik bo'lsa, obuna bor deb o'tkazib yubormaymiz.
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
            "❌ Hali barcha kanallarga obuna bo'lmagansiz.\n\n"
            "Quyidagi kanallarga obuna bo'ling, keyin yana «✅ Tasdiqlash»ni bosing.",
            reply_markup=subscription_keyboard()
        )
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎥 Kinolar kanaliga o'tish", url=MOVIES_CHANNEL_URL)]
    ])
    await query.edit_message_text(
        "✅ Obuna tasdiqlandi!\n\n"
        "🎬 Barcha kinolarimiz ushbu kanalda. Marhamat, kanalimizga o'ting!",
        reply_markup=keyboard
    )


def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "BOT_TOKEN topilmadi. Hosting sozlamalarida BOT_TOKEN nomli "
            "environment variable yarating va yangi tokenni uning qiymatiga qo'ying."
        )

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    logger.info("TimeKinolar bot ishga tushmoqda...")
    app.run_polling()


if __name__ == "__main__":
    main()
