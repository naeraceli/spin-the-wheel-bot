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
# IMAGE MAPPING
# ==========================================

PRIZE_IMAGES = {
    "🎟️ Voucher diskon 25% untuk orderan custom": {
        "spin": "images/spin_25.png",
        "claimed": None,
    },

    "🎟️ Voucher diskon 35% untuk orderan custom": {
        "spin": "images/spin_35.png",
        "claimed": None,
    },

    "🎁 Free claim catalog costless": {
        "spin": "images/spin_costless.png",
        "claimed": None,
    },

    "🚀 1 Daily Boost": {
        "spin": "images/spin_daily.png",
        "claimed": None,
    },

    "🚀 1 Weekly Boost": {
        "spin": "images/spin_weekly.png",
        "claimed": None,
    },

    "🚀 1 Monthly Boost": {
        "spin": "images/spin_monthly.png",
        "claimed": None,
    },

    "⭐ Gift 15 Stars": {
        "spin": "images/spin_15s.png",
        "claimed": None,
    },

    "⭐ Gift 25 Stars": {
        "spin": "images/spin_25s.png",
        "claimed": None,
    },

    "⭐ Gift 50 Stars": {
        "spin": "images/spin_50s.png",
        "claimed": None,
    },
}

# ==========================================
# PERSISTENT STORAGE
# ==========================================

DATA_DIR = os.getenv("DATA_DIR", "/data")
DATA_FILE = os.path.join(DATA_DIR, "chat_prizes.json")


def load_all_chat_prizes():
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(DATA_FILE):
        save_all_chat_prizes({})
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        save_all_chat_prizes({})
        return {}


def save_all_chat_prizes(all_chat_prizes):
    os.makedirs(DATA_DIR, exist_ok=True)

    temporary_file = DATA_FILE + ".tmp"

    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(
            all_chat_prizes,
            file,
            ensure_ascii=False,
            indent=4,
        )

    os.replace(temporary_file, DATA_FILE)


all_chat_prizes = load_all_chat_prizes()

# ==========================================
# GET / CREATE INVENTORY FOR CHAT
# ==========================================


def get_chat_prizes(chat_id):
    chat_key = str(chat_id)

    if chat_key not in all_chat_prizes:
        all_chat_prizes[chat_key] = INITIAL_PRIZES.copy()
        save_all_chat_prizes(all_chat_prizes)

    return all_chat_prizes[chat_key]


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
# BUTTONS
# ==========================================


def spin_keyboard():
    return InlineKeyboardMarkup(
        [
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
    )


# ==========================================
# AVAILABLE PRIZES
# ==========================================


def get_available_prizes(chat_id):
    chat_prizes = get_chat_prizes(chat_id)

    return [
        prize
        for prize, quantity in chat_prizes.items()
        if quantity > 0
    ]


# ==========================================
# SEND NEW SPIN
# ==========================================


async def send_new_spin_message(
    chat_id,
    context,
):
    available_prizes = get_available_prizes(chat_id)

    if not available_prizes:
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "🎡 *The Spin the Wheel is empty!*\n\n"
                "All prizes in this chat have been claimed. 🎁\n\n"
                "Use /reload to restore all prize slots."
            ),
            parse_mode="Markdown",
        )
        return None

    selected_prize = random.choice(
        available_prizes
    )

    context.user_data["current_prize"] = selected_prize
    context.user_data["current_chat_id"] = chat_id

    # ======================================
    # SPIN IMAGE
    # ======================================

    image_path = PRIZE_IMAGES.get(
        selected_prize,
        {}
    ).get("spin")

    if (
        image_path
        and os.path.exists(image_path)
    ):
        with open(
            image_path,
            "rb"
        ) as image_file:

            message = await context.bot.send_photo(
                chat_id=chat_id,
                photo=image_file,
                caption=(
                    "🎡 *SPINNING...*\n\n"
                    f"🎁 *Your prize:* {selected_prize}\n\n"
                    "Congratulations! 🥳"
                ),
                reply_markup=spin_keyboard(),
                parse_mode="Markdown",
            )

    else:
        message = await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "🎡 *SPINNING...*\n\n"
                f"🎁 *Your prize:* {selected_prize}\n\n"
                "Congratulations! 🥳"
            ),
            reply_markup=spin_keyboard(),
            parse_mode="Markdown",
        )

    context.user_data["current_spin_message_id"] = (
        message.message_id
    )

    return message


# ==========================================
# /START
# ==========================================


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(
        update.effective_user.id
    ):
        await deny_access(update)
        return

    await update.message.reply_text(
        "🎡 Welcome to the Spin the Wheel!\n\n"
        "Use /spin to start spinning.\n"
        "Use /reload to restore all prize slots."
    )


# ==========================================
# /SPIN
# ==========================================


async def spin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(
        update.effective_user.id
    ):
        await deny_access(update)
        return

    chat_id = update.effective_chat.id

    context.user_data["current_prize"] = None
    context.user_data["waiting_for_username"] = False
    context.user_data["current_chat_id"] = chat_id
    context.user_data["current_spin_message_id"] = None

    await send_new_spin_message(
        chat_id,
        context,
    )


# ==========================================
# /RELOAD
# ==========================================


async def reload_prizes(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(
        update.effective_user.id
    ):
        await deny_access(update)
        return

    chat_id = update.effective_chat.id
    chat_key = str(chat_id)

    # Restore full inventory ONLY for this chat.
    all_chat_prizes[chat_key] = (
        INITIAL_PRIZES.copy()
    )

    save_all_chat_prizes(
        all_chat_prizes
    )

    # Reset current spin session.
    context.user_data["current_prize"] = None
    context.user_data["waiting_for_username"] = False
    context.user_data["current_chat_id"] = None
    context.user_data["current_spin_message_id"] = None

    await update.message.reply_text(
        "🔄 *RELOADED!*\n\n"
        "All 15 prize slots have been restored "
        "for this chat. 🎡✨",
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

    if not is_admin(
        query.from_user.id
    ):
        await query.answer(
            "⚠️ Only admins can control the Spin the Wheel.",
            show_alert=True,
        )
        return

    current_message_id = (
        context.user_data.get(
            "current_spin_message_id"
        )
    )

    if (
        query.message.message_id
        != current_message_id
    ):
        await query.answer(
            "⚠️ This spin is no longer active.",
            show_alert=True,
        )
        return

    await query.answer()

    if query.data == "next_spin":
        await next_spin(
            query,
            context,
        )

    elif query.data == "claim_prize":
        await claim_prize(
            query,
            context,
        )


# ==========================================
# NEXT
# ==========================================


async def next_spin(
    query,
    context,
):
    try:
        await query.edit_message_reply_markup(
            reply_markup=None
        )
    except Exception:
        pass

    chat_id = query.message.chat_id

    await send_new_spin_message(
        chat_id,
        context,
    )


# ==========================================
# CLAIM
# ==========================================


async def claim_prize(
    query,
    context,
):
    selected_prize = (
        context.user_data.get(
            "current_prize"
        )
    )

    chat_id = query.message.chat_id

    if not selected_prize:
        await query.answer(
            "⚠️ There is no active prize to claim.",
            show_alert=True,
        )
        return

    chat_prizes = get_chat_prizes(
        chat_id
    )

    if (
        chat_prizes.get(
            selected_prize,
            0
        )
        <= 0
    ):
        await query.edit_message_reply_markup(
            reply_markup=None
        )

        await query.answer(
            "⚠️ Sorry, this prize has already been claimed.",
            show_alert=True,
        )

        return

    await query.edit_message_reply_markup(
        reply_markup=None
    )

    context.user_data[
        "waiting_for_username"
    ] = True

    context.user_data[
        "current_chat_id"
    ] = chat_id

    await query.message.reply_text(
        "🎁 *Prize selected!*\n\n"
        f"🎁 *Prize:* {selected_prize}\n\n"
        "👤 Please send the buyer's username.\n"
        "Example: `@username`",
        parse_mode="Markdown",
    )


# ==========================================
# RECEIVE USERNAME
# ==========================================


async def receive_username(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(
        update.effective_user.id
    ):
        await deny_access(update)
        return

    if not context.user_data.get(
        "waiting_for_username"
    ):
        return

    username = (
        update.message.text.strip()
    )

    selected_prize = (
        context.user_data.get(
            "current_prize"
        )
    )

    chat_id = update.effective_chat.id

    if not selected_prize:
        context.user_data[
            "waiting_for_username"
        ] = False

        await update.message.reply_text(
            "⚠️ There is no active prize to claim."
        )

        return

    if (
        context.user_data.get(
            "current_chat_id"
        )
        != chat_id
    ):
        await update.message.reply_text(
            "⚠️ Please finish the active claim "
            "in the original chat."
        )

        return

    chat_prizes = get_chat_prizes(
        chat_id
    )

    if (
        chat_prizes.get(
            selected_prize,
            0
        )
        <= 0
    ):
        context.user_data[
            "waiting_for_username"
        ] = False

        await update.message.reply_text(
            "⚠️ Sorry, this prize has already been claimed."
        )

        return

    # ======================================
    # REDUCE STOCK FOR THIS CHAT ONLY
    # ======================================

    chat_prizes[
        selected_prize
    ] -= 1

    remaining = chat_prizes[
        selected_prize
    ]

    if remaining <= 0:
        del chat_prizes[
            selected_prize
        ]

    all_chat_prizes[
        str(chat_id)
    ] = chat_prizes

    save_all_chat_prizes(
        all_chat_prizes
    )

    # ======================================
    # RESET SESSION
    # ======================================

    context.user_data[
        "waiting_for_username"
    ] = False

    context.user_data[
        "current_prize"
    ] = None

    context.user_data[
        "current_chat_id"
    ] = None

    context.user_data[
        "current_spin_message_id"
    ] = None

    # ======================================
    # CLAIMED RESULT
    # ======================================

    if remaining <= 0:
        stock_message = (
            "🚫 This prize is now sold out "
            "in this chat and has been removed "
            "from the wheel."
        )

    else:
        stock_message = (
            f"📦 Remaining slots for this prize: "
            f"*{remaining}*"
        )

    claimed_image = (
        PRIZE_IMAGES.get(
            selected_prize,
            {}
        ).get("claimed")
    )

    claimed_caption = (
        "🎉 *CLAIMED!*\n\n"
        f"👤 *Buyer:* {username}\n"
        f"🎁 *Prize:* {selected_prize}\n\n"
        f"{stock_message}"
    )

    if (
        claimed_image
        and os.path.exists(
            claimed_image
        )
    ):
        with open(
            claimed_image,
            "rb"
        ) as image_file:

            await update.message.reply_photo(
                photo=image_file,
                caption=claimed_caption,
                parse_mode="Markdown",
            )

    else:
        await update.message.reply_text(
            claimed_caption,
            parse_mode="Markdown",
        )


# ==========================================
# MAIN
# ==========================================


def main():
    token = os.getenv(
        "BOT_TOKEN"
    )

    if not token:
        raise ValueError(
            "BOT_TOKEN is not set!"
        )

    application = (
        Application.builder()
        .token(token)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "spin",
            spin
        )
    )

    application.add_handler(
        CommandHandler(
            "reload",
            reload_prizes
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            receive_username,
        )
    )

    print(
        "Spin the Wheel bot is running..."
    )

    application.run_polling()


if __name__ == "__main__":
    main()
