import json
import os
import random

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


# ==========================================
# ADMIN IDs
# ==========================================

ADMIN_IDS = {
    1575941037,
    5034853948,
    7837544498,
    7072320975,
    7281591437,
}


# ==========================================
# INITIAL PRIZE INVENTORY
# ==========================================

INITIAL_PRIZES = {
    "🎟️ Voucher diskon 25% untuk orderan custom": 4,
    "🎟️ Voucher diskon 35% untuk orderan custom": 2,
    "🎁 Free claim catalog costless": 3,
    "🚀 1 Daily Boost": 1,
    "🚀 1 Weekly Boost": 1,
    "🚀 1 Monthly Boost": 1,
    "⭐ Gift 15 Stars": 1,
    "⭐ Gift 25 Stars": 1,
    "⭐ Gift 50 Stars": 1,
}


# ==========================================
# PERSISTENT STORAGE
# ==========================================

DATA_DIR = os.getenv("DATA_DIR", "/data")
DATA_FILE = os.path.join(DATA_DIR, "prizes.json")


def load_prizes():
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(DATA_FILE):
        prizes = INITIAL_PRIZES.copy()
        save_prizes(prizes)
        return prizes

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        prizes = INITIAL_PRIZES.copy()
        save_prizes(prizes)
        return prizes


def save_prizes(prizes):
    os.makedirs(DATA_DIR, exist_ok=True)

    temporary_file = DATA_FILE + ".tmp"

    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(
            prizes,
            file,
            ensure_ascii=False,
            indent=4,
        )

    os.replace(temporary_file, DATA_FILE)


prizes = load_prizes()


# ==========================================
# ADMIN CHECK
# ==========================================

def is_admin(user_id):
    return user_id in ADMIN_IDS


async def deny_access(update: Update):
    if update.callback_query:
        await update.callback_query.answer(
            "⚠️ Only admins can control the Spin the Wheel.",
            show_alert=True,
        )

    elif update.message:
        await update.message.reply_text(
            "⚠️ Only admins can control the Spin the Wheel."
        )


# ==========================================
# /START
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await deny_access(update)
        return

    await update.message.reply_text(
        "🎡 Welcome to the Spin the Wheel!\n\n"
        "Use /spin to start spinning."
    )


# ==========================================
# /SPIN
# ==========================================

async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await deny_access(update)
        return

    available_prizes = [
        prize
        for prize, quantity in prizes.items()
        if quantity > 0
    ]

    if not available_prizes:
        await update.message.reply_text(
            "🎡 The Spin the Wheel is empty!\n\n"
            "All prizes have been claimed. 🎁"
        )
        return

    selected_prize = random.choice(available_prizes)

    context.user_data["current_prize"] = selected_prize

    keyboard = [
        [
            InlineKeyboardButton(
                "🔄 NEXT",
                callback_data="next_spin",
            ),
            InlineKeyboardButton(
                "🎁 CLAIM",
                callback_data="claim_prize",
            ),
        ]
    ]

    await update.message.reply_text(
        "🎡 *SPINNING...*\n\n"
        f"🎁 *Your prize:* {selected_prize}\n\n"
        "Congratulations! 🥳",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


# ==========================================
# BUTTON HANDLER
# ==========================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not is_admin(query.from_user.id):
        await query.answer(
            "⚠️ Only admins can control the Spin the Wheel.",
            show_alert=True,
        )
        return

    await query.answer()

    if query.data == "next_spin":
        await next_spin(query, context)

    elif query.data == "claim_prize":
        await claim_prize(query, context)


# ==========================================
# NEXT
# ==========================================

async def next_spin(query, context):
    available_prizes = [
        prize
        for prize, quantity in prizes.items()
        if quantity > 0
    ]

    if not available_prizes:
        await query.edit_message_text(
            "🎡 The Spin the Wheel is empty!\n\n"
            "All prizes have been claimed. 🎁"
        )
        return

    selected_prize = random.choice(available_prizes)

    context.user_data["current_prize"] = selected_prize

    keyboard = [
        [
            InlineKeyboardButton(
                "🔄 NEXT",
                callback_data="next_spin",
            ),
            InlineKeyboardButton(
                "🎁 CLAIM",
                callback_data="claim_prize",
            ),
        ]
    ]

    await query.edit_message_text(
        "🎡 *SPINNING...*\n\n"
        f"🎁 *Your prize:* {selected_prize}\n\n"
        "Congratulations! 🥳",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


# ==========================================
# CLAIM
# ==========================================

async def claim_prize(query, context):
    selected_prize = context.user_data.get("current_prize")

    if not selected_prize:
        await query.edit_message_text(
            "⚠️ There is no active prize to claim."
        )
        return

    if prizes.get(selected_prize, 0) <= 0:
        await query.edit_message_text(
            "⚠️ Sorry, this prize has already been claimed."
        )
        return

    context.user_data["waiting_for_username"] = True

    await query.edit_message_text(
        "🎁 *Prize selected!*\n\n"
        f"🎁 *Prize:* {selected_prize}\n\n"
        "👤 Please send the buyer's username.\n"
        "Example: `@username`",
        parse_mode="Markdown",
    )


# ==========================================
# RECEIVE BUYER USERNAME
# ==========================================

async def receive_username(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(update.effective_user.id):
        await deny_access(update)
        return

    if not context.user_data.get("waiting_for_username"):
        return

    username = update.message.text.strip()

    selected_prize = context.user_data.get("current_prize")

    if not selected_prize:
        context.user_data["waiting_for_username"] = False

        await update.message.reply_text(
            "⚠️ There is no active prize to claim."
        )
        return

    if prizes.get(selected_prize, 0) <= 0:
        context.user_data["waiting_for_username"] = False

        await update.message.reply_text(
            "⚠️ Sorry, this prize has already been claimed."
        )
        return

    # Reduce stock ONLY after the buyer username is submitted.
    prizes[selected_prize] -= 1

    remaining = prizes[selected_prize]

    if remaining <= 0:
        del prizes[selected_prize]

    save_prizes(prizes)

    context.user_data["waiting_for_username"] = False
    context.user_data["current_prize"] = None

    if remaining <= 0:
        stock_message = (
            "🚫 This prize is now sold out "
            "and has been removed from the wheel."
        )
    else:
        stock_message = (
            f"📦 Remaining slots for this prize: *{remaining}*"
        )

    await update.message.reply_text(
        "🎉 *CLAIMED!*\n\n"
        f"👤 *Buyer:* {username}\n"
        f"🎁 *Prize:* {selected_prize}\n\n"
        f"{stock_message}",
        parse_mode="Markdown",
    )


# ==========================================
# MAIN
# ==========================================

def main():
    token = os.getenv("BOT_TOKEN")

    if not token:
        raise ValueError("BOT_TOKEN is not set!")

    application = Application.builder().token(token).build()

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("spin", spin)
    )

    application.add_handler(
        CallbackQueryHandler(button_handler)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_username,
        )
    )

    print("Spin the Wheel bot is running...")

    application.run_polling()


if __name__ == "__main__":
    main()
