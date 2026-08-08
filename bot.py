import os
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


# =========================
# 15 SPIN THE WHEEL SLOTS
# =========================

PRIZES = {
    1: "🎟️ Voucher diskon 25% untuk orderan custom",
    2: "🎟️ Voucher diskon 25% untuk orderan custom",
    3: "🎟️ Voucher diskon 25% untuk orderan custom",
    4: "🎟️ Voucher diskon 25% untuk orderan custom",

    5: "🎟️ Voucher diskon 35% untuk orderan custom",
    6: "🎟️ Voucher diskon 35% untuk orderan custom",

    7: "🎁 Free claim catalog costless",
    8: "🎁 Free claim catalog costless",
    9: "🎁 Free claim catalog costless",

    10: "🚀 1 Daily Boost",
    11: "🚀 1 Weekly Boost",
    12: "🚀 1 Monthly Boost",

    13: "⭐ Gift 15 Stars",
    14: "⭐ Gift 25 Stars",
    15: "⭐ Gift 50 Stars",
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎡 Welcome to the Spin the Wheel!\n\n"
        "Ready to try your luck? ✨\n"
        "Use /spin to spin the wheel!"
    )


async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = random.randint(1, 15)
    prize = PRIZES[number]

    await update.message.reply_text(
        "🎡 *SPINNING...*\n\n"
        f"✨ Your slot: *{number}*\n"
        f"🎁 Your prize: *{prize}*\n\n"
        "Congratulations! 🥳",
        parse_mode="Markdown"
    )


def main():
    token = os.getenv("BOT_TOKEN")

    if not token:
        raise ValueError("BOT_TOKEN is not set!")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("spin", spin))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
