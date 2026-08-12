import json
import os
import random
from datetime import datetime, timezone

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)


# =========================================================
# ADMIN IDS
# =========================================================

ADMIN_IDS = {
    1575941037,
    7281591437,
}


# =========================================================
# INITIAL PRIZE INVENTORY
# =========================================================

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


# =========================================================
# IMAGE MAPPING
# =========================================================

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


# =========================================================
# PERSISTENT STORAGE
# =========================================================

DATA_DIR = os.getenv(
    "DATA_DIR",
    "/data",
)

PRIZES_FILE = os.path.join(
    DATA_DIR,
    "global_prizes.json",
)

USERS_FILE = os.path.join(
    DATA_DIR,
    "participants.json",
)

CLAIMS_FILE = os.path.join(
    DATA_DIR,
    "claim_history.json",
)

SETTINGS_FILE = os.path.join(
    DATA_DIR,
    "bot_settings.json",
)


def ensure_data_dir():
    os.makedirs(
        DATA_DIR,
        exist_ok=True,
    )


def save_json(
    file_path,
    data,
):
    ensure_data_dir()

    temporary_file = (
        file_path + ".tmp"
    )

    with open(
        temporary_file,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4,
        )

    os.replace(
        temporary_file,
        file_path,
    )


def load_json(
    file_path,
    default,
):
    ensure_data_dir()

    if not os.path.exists(
        file_path
    ):
        save_json(
            file_path,
            default,
        )
        return default

    try:
        with open(
            file_path,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except (
        json.JSONDecodeError,
        OSError,
    ):
        save_json(
            file_path,
            default,
        )
        return default


# =========================================================
# LOAD DATABASES
# =========================================================

global_prizes = load_json(
    PRIZES_FILE,
    INITIAL_PRIZES.copy(),
)

participants = load_json(
    USERS_FILE,
    {},
)

claim_history = load_json(
    CLAIMS_FILE,
    [],
)

settings = load_json(
    SETTINGS_FILE,
    {
        "announcement_group_id": None,
    },
)


# =========================================================
# ADMIN CHECK
# =========================================================

def is_admin(user_id):
    return user_id in ADMIN_IDS


async def admin_only(update):
    user_id = update.effective_user.id

    if is_admin(user_id):
        return True

    if update.message:
        await update.message.reply_text(
            "⚠️ This command is for admins only."
        )

    return False


# =========================================================
# PRIZE HELPERS
# =========================================================

def get_available_prizes():
    return [
        prize
        for prize, quantity
        in global_prizes.items()
        if quantity > 0
    ]


def total_initial_prizes():
    return sum(
        INITIAL_PRIZES.values()
    )


def total_remaining_prizes():
    return sum(
        global_prizes.values()
    )


# =========================================================
# PARTICIPANT HELPERS
# =========================================================

def get_participant(user_id):
    return participants.get(
        str(user_id)
    )


def save_participants():
    save_json(
        USERS_FILE,
        participants,
    )


def get_remaining_spins(
    user_id,
):
    participant = get_participant(
        user_id
    )

    if not participant:
        return 0

    return max(
        0,
        participant.get(
            "max_spins",
            0,
        )
        - participant.get(
            "spins_used",
            0,
        ),
    )


def can_start_spin(
    user_id,
):
    participant = get_participant(
        user_id
    )

    if not participant:
        return False

    if participant.get(
        "status"
    ) != "active":
        return False

    if participant.get(
        "claimed",
        False,
    ):
        return False

    return (
        participant.get(
            "spins_used",
            0,
        )
        < participant.get(
            "max_spins",
            0,
        )
    )


# =========================================================
# USER DISPLAY NAME
# =========================================================

def get_user_display_name(user):
    if user.username:
        return f"@{user.username}"

    if user.full_name:
        return user.full_name

    return str(user.id)


# =========================================================
# KEYBOARDS
# =========================================================

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


def start_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎡 SPIN",
                    callback_data="start_spin",
                )
            ]
        ]
    )


# =========================================================
# /START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    user_id = user.id

    # Admin
    if is_admin(user_id):
        await update.message.reply_text(
            "👑 *Spin the Wheel Admin Panel*\n\n"
            "Available commands:\n\n"
            "`/grant USER_ID SPINS`\n"
            "`/status USER_ID`\n"
            "`/revoke USER_ID`\n"
            "`/setgroup`\n"
            "`/claims`\n"
            "`/reload`\n"
            "`/clearclaims`",
            parse_mode="Markdown",
        )
        return

    participant = get_participant(
        user_id
    )

    if not participant:
        await update.message.reply_text(
            "🎡 *Spin the Wheel*\n\n"
            "You don't have an active Spin session yet.\n\n"
            "Please contact the event admin.",
            parse_mode="Markdown",
        )
        return

    if participant.get(
        "status"
    ) != "active":
        await update.message.reply_text(
            "🔒 Your Spin session is no longer active."
        )
        return

    remaining = get_remaining_spins(
        user_id
    )

    await update.message.reply_text(
        "🎡 *Welcome to Spin the Wheel!*\n\n"
        f"🔢 Spins remaining: *{remaining}*\n\n"
        "Ready to play?",
        reply_markup=start_keyboard(),
        parse_mode="Markdown",
    )


# =========================================================
# SPIN RESULT
# =========================================================

async def perform_spin(
    user_id,
    context,
):
    participant = get_participant(
        user_id
    )

    if not participant:
        return

    if not can_start_spin(
        user_id
    ):
        return

    available_prizes = (
        get_available_prizes()
    )

    if not available_prizes:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🎡 *The Spin the Wheel is empty!*\n\n"
                "All prizes have been claimed."
            ),
            parse_mode="Markdown",
        )
        return

    selected_prize = random.choice(
        available_prizes
    )

    # ======================================
    # COUNT THIS SPIN
    # ======================================

    participant[
        "spins_used"
    ] += 1

    participant[
        "current_prize"
    ] = selected_prize

    save_participants()

    spins_used = participant[
        "spins_used"
    ]

    max_spins = participant[
        "max_spins"
    ]

    is_final_spin = (
        spins_used >= max_spins
    )

    # ======================================
    # FINAL SPIN = AUTO CLAIM
    # ======================================

    if is_final_spin:
        await auto_claim_prize(
            user_id,
            selected_prize,
            context,
        )
        return

    # ======================================
    # NORMAL SPIN
    # ======================================

    remaining = (
        max_spins
        - spins_used
    )

    image_path = (
        PRIZE_IMAGES
        .get(
            selected_prize,
            {},
        )
        .get("spin")
    )

    caption = (
        "🎡 *SPIN RESULT!*\n\n"
        f"🎁 *Your prize:* {selected_prize}\n\n"
        f"🔢 Spins remaining: *{remaining}*\n\n"
        "Choose an action below."
    )

    if (
        image_path
        and os.path.exists(
            image_path
        )
    ):
        with open(
            image_path,
            "rb",
        ) as image_file:

            await context.bot.send_photo(
                chat_id=user_id,
                photo=image_file,
                caption=caption,
                reply_markup=spin_keyboard(),
                parse_mode="Markdown",
            )

    else:
        await context.bot.send_message(
            chat_id=user_id,
            text=caption,
            reply_markup=spin_keyboard(),
            parse_mode="Markdown",
        )


# =========================================================
# /SPIN
# =========================================================

async def spin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id

    if is_admin(user_id):
        await update.message.reply_text(
            "👑 Admin accounts cannot use participant sessions."
        )
        return

    participant = get_participant(
        user_id
    )

    if not participant:
        await update.message.reply_text(
            "⚠️ You don't have an active Spin session."
        )
        return

    if participant.get(
        "claimed",
        False,
    ):
        await update.message.reply_text(
            "🔒 Your session has already ended because you claimed a prize."
        )
        return

    if participant.get(
        "status"
    ) != "active":
        await update.message.reply_text(
            "🔒 Your Spin session is no longer active."
        )
        return

    if not can_start_spin(
        user_id
    ):
        await update.message.reply_text(
            "🚫 You have no spins remaining."
        )
        return

    await perform_spin(
        user_id,
        context,
    )


# =========================================================
# BUTTON HANDLER
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    user_id = query.from_user.id

    # ======================================
    # START SPIN BUTTON
    # ======================================

    if query.data == "start_spin":
        participant = get_participant(
            user_id
        )

        if not participant:
            await query.answer(
                "⚠️ You don't have an active session.",
                show_alert=True,
            )
            return

        if not can_start_spin(
            user_id
        ):
            await query.answer(
                "🚫 You cannot spin anymore.",
                show_alert=True,
            )
            return

        await query.answer()

        try:
            await query.edit_message_reply_markup(
                reply_markup=None
            )
        except Exception:
            pass

        await perform_spin(
            user_id,
            context,
        )

        return

    # ======================================
    # NORMAL PARTICIPANT BUTTONS
    # ======================================

    participant = get_participant(
        user_id
    )

    if not participant:
        await query.answer(
            "⚠️ You don't have an active session.",
            show_alert=True,
        )
        return

    if participant.get(
        "status"
    ) != "active":
        await query.answer(
            "🔒 Your session is no longer active.",
            show_alert=True,
        )
        return

    if participant.get(
        "claimed",
        False,
    ):
        await query.answer(
            "🔒 Your session has ended.",
            show_alert=True,
        )
        return

    selected_prize = participant.get(
        "current_prize"
    )

    if not selected_prize:
        await query.answer(
            "⚠️ There is no active prize.",
            show_alert=True,
        )
        return

    # ======================================
    # NEXT
    # ======================================

    if query.data == "next_spin":
        if not can_start_spin(
            user_id
        ):
            await query.answer(
                "🚫 You have no spins remaining.",
                show_alert=True,
            )
            return

        await query.answer()

        participant[
            "current_prize"
        ] = None

        save_participants()

        try:
            await query.edit_message_reply_markup(
                reply_markup=None
            )
        except Exception:
            pass

        await perform_spin(
            user_id,
            context,
        )

        return

    # ======================================
    # CLAIM
    # ======================================

    if query.data == "claim_prize":
        await claim_prize(
            query,
            context,
        )


# =========================================================
# CLAIM PRIZE
# =========================================================

async def claim_prize(
    query,
    context,
):
    user_id = query.from_user.id

    participant = get_participant(
        user_id
    )

    if not participant:
        await query.answer(
            "⚠️ No active session.",
            show_alert=True,
        )
        return

    selected_prize = participant.get(
        "current_prize"
    )

    if not selected_prize:
        await query.answer(
            "⚠️ There is no active prize.",
            show_alert=True,
        )
        return

    current_stock = global_prizes.get(
        selected_prize,
        0,
    )

    if current_stock <= 0:
        await query.answer(
            "⚠️ Sorry, this prize has already been claimed by someone else.",
            show_alert=True,
        )

        participant[
            "current_prize"
        ] = None

        save_participants()

        return

    await query.answer(
        "🎉 Prize claimed!",
        show_alert=True,
    )

    try:
        await query.edit_message_reply_markup(
            reply_markup=None
        )
    except Exception:
        pass

    await finalize_claim(
        user_id,
        selected_prize,
        context,
        automatic=False,
    )


# =========================================================
# AUTO CLAIM FINAL SPIN
# =========================================================

async def auto_claim_prize(
    user_id,
    selected_prize,
    context,
):
    await finalize_claim(
        user_id,
        selected_prize,
        context,
        automatic=True,
    )


# =========================================================
# FINALIZE CLAIM
# =========================================================

async def finalize_claim(
    user_id,
    selected_prize,
    context,
    automatic=False,
):
    participant = get_participant(
        user_id
    )

    if not participant:
        return

    current_stock = global_prizes.get(
        selected_prize,
        0,
    )

    # ======================================
    # PRIZE ALREADY GONE
    # ======================================

    if current_stock <= 0:
        participant[
            "current_prize"
        ] = None

        participant[
            "status"
        ] = "active"

        save_participants()

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "⚠️ Unfortunately, this prize "
                "was claimed by another participant "
                "before it could be confirmed.\n\n"
                "Please contact the event admin."
            ),
        )

        return

    # ======================================
    # REDUCE GLOBAL STOCK
    # ======================================

    global_prizes[
        selected_prize
    ] -= 1

    remaining_stock = global_prizes[
        selected_prize
    ]

    if remaining_stock <= 0:
        del global_prizes[
            selected_prize
        ]

    save_json(
        PRIZES_FILE,
        global_prizes,
    )

    # ======================================
    # END PARTICIPANT SESSION
    # ======================================

    participant[
        "claimed"
    ] = True

    participant[
        "status"
    ] = "ended"

    participant[
        "current_prize"
    ] = None

    save_participants()

    # ======================================
    # CLAIM HISTORY
    # ======================================

    user = None

    try:
        user = await context.bot.get_chat(
            user_id
        )
    except Exception:
        pass

    if user:
        display_name = get_user_display_name(
            user
        )
    else:
        display_name = str(
            user_id
        )

    claim_record = {
        "user_id": user_id,
        "username": display_name,
        "prize": selected_prize,
        "automatic": automatic,
        "claimed_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    claim_history.append(
        claim_record
    )

    save_json(
        CLAIMS_FILE,
        claim_history,
    )

    # ======================================
    # PRIVATE RESULT
    # ======================================

    if automatic:
        title = (
            "🏁 *FINAL SPIN — AUTO CLAIMED!*"
        )
    else:
        title = (
            "🎉 *PRIZE CLAIMED!*"
        )

    if remaining_stock <= 0:
        stock_message = (
            "🚫 This prize is now sold out globally."
        )
    else:
        stock_message = (
            f"📦 Remaining global stock: "
            f"*{remaining_stock}*"
        )

    private_caption = (
        f"{title}\n\n"
        f"🎁 *Prize:* {selected_prize}\n\n"
        f"{stock_message}\n\n"
        "🔒 Your Spin session has ended."
    )

    claimed_image = (
        PRIZE_IMAGES
        .get(
            selected_prize,
            {},
        )
        .get("claimed")
    )

    if (
        claimed_image
        and os.path.exists(
            claimed_image
        )
    ):
        with open(
            claimed_image,
            "rb",
        ) as image_file:

            await context.bot.send_photo(
                chat_id=user_id,
                photo=image_file,
                caption=private_caption,
                parse_mode="Markdown",
            )

    else:
        await context.bot.send_message(
            chat_id=user_id,
            text=private_caption,
            parse_mode="Markdown",
        )

    # ======================================
    # GROUP ANNOUNCEMENT
    # ======================================

    await announce_claim_to_group(
        user_id,
        display_name,
        selected_prize,
        automatic,
        context,
    )


# =========================================================
# GROUP ANNOUNCEMENT
# =========================================================

async def announce_claim_to_group(
    user_id,
    display_name,
    selected_prize,
    automatic,
    context,
):
    group_id = settings.get(
        "announcement_group_id"
    )

    if not group_id:
        return

    if automatic:
        header = (
            "🏁 *FINAL SPIN — AUTO CLAIMED!*"
        )
    else:
        header = (
            "🎉 *PRIZE CLAIMED!*"
        )

    message = (
        f"{header}\n\n"
        f"👤 *Participant:* {display_name}\n"
        f"🆔 User ID: `{user_id}`\n"
        f"🎁 *Prize:* {selected_prize}\n\n"
        "Congratulations! 🥳🎡"
    )

    try:
        await context.bot.send_message(
            chat_id=group_id,
            text=message,
            parse_mode="Markdown",
        )

    except Exception as error:
        print(
            "Failed to announce claim "
            f"to group: {error}"
        )


# =========================================================
# /GRANT
# =========================================================

async def grant(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await admin_only(update):
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "Usage:\n"
            "`/grant USER_ID SPINS`\n\n"
            "Example:\n"
            "`/grant 123456789 4`",
            parse_mode="Markdown",
        )
        return

    try:
        target_user_id = int(
            context.args[0]
        )

        max_spins = int(
            context.args[1]
        )

    except ValueError:
        await update.message.reply_text(
            "⚠️ USER_ID and SPINS must be numbers."
        )
        return

    if max_spins <= 0:
        await update.message.reply_text(
            "⚠️ Spin amount must be greater than 0."
        )
        return

    participants[
        str(target_user_id)
    ] = {
        "user_id": target_user_id,
        "max_spins": max_spins,
        "spins_used": 0,
        "status": "active",
        "claimed": False,
        "current_prize": None,
        "granted_by": update.effective_user.id,
        "granted_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    save_participants()

    await update.message.reply_text(
        "✅ *ACCESS GRANTED!*\n\n"
        f"👤 User ID: `{target_user_id}`\n"
        f"🎡 Maximum spins: *{max_spins}*\n"
        f"🔢 Remaining: *{max_spins}*",
        parse_mode="Markdown",
    )


# =========================================================
# /STATUS
# =========================================================

async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await admin_only(update):
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "Usage:\n"
            "`/status USER_ID`",
            parse_mode="Markdown",
        )
        return

    try:
        target_user_id = int(
            context.args[0]
        )

    except ValueError:
        await update.message.reply_text(
            "⚠️ USER_ID must be a number."
        )
        return

    participant = get_participant(
        target_user_id
    )

    if not participant:
        await update.message.reply_text(
            "❌ No participant record found."
        )
        return

    max_spins = participant.get(
        "max_spins",
        0,
    )

    spins_used = participant.get(
        "spins_used",
        0,
    )

    remaining = max(
        0,
        max_spins - spins_used,
    )

    status_text = participant.get(
        "status",
        "unknown",
    )

    claimed = participant.get(
        "claimed",
        False,
    )

    await update.message.reply_text(
        "👤 *PARTICIPANT STATUS*\n\n"
        f"🆔 User ID: `{target_user_id}`\n"
        f"🎡 Maximum spins: *{max_spins}*\n"
        f"🎯 Spins used: *{spins_used}*\n"
        f"🔢 Remaining: *{remaining}*\n"
        f"📌 Status: *{status_text.upper()}*\n"
        f"🎁 Claimed: *{'YES' if claimed else 'NO'}*",
        parse_mode="Markdown",
    )


# =========================================================
# /REVOKE
# =========================================================

async def revoke(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await admin_only(update):
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "Usage:\n"
            "`/revoke USER_ID`",
            parse_mode="Markdown",
        )
        return

    try:
        target_user_id = int(
            context.args[0]
        )

    except ValueError:
        await update.message.reply_text(
            "⚠️ USER_ID must be a number."
        )
        return

    participant = get_participant(
        target_user_id
    )

    if not participant:
        await update.message.reply_text(
            "❌ No participant record found."
        )
        return

    participant[
        "status"
    ] = "revoked"

    participant[
        "current_prize"
    ] = None

    save_participants()

    await update.message.reply_text(
        "🔒 *ACCESS REVOKED!*\n\n"
        f"👤 User ID: `{target_user_id}`\n\n"
        "This participant can no longer use the Spin the Wheel.",
        parse_mode="Markdown",
    )


# =========================================================
# /SETGROUP
# =========================================================

async def set_group(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await admin_only(update):
        return

    chat = update.effective_chat

    # Only useful inside a group.
    if chat.type not in (
        "group",
        "supergroup",
    ):
        await update.message.reply_text(
            "⚠️ Use `/setgroup` inside the group "
            "where you want claim announcements "
            "to be sent.",
            parse_mode="Markdown",
        )
        return

    settings[
        "announcement_group_id"
    ] = chat.id

    save_json(
        SETTINGS_FILE,
        settings,
    )

    await update.message.reply_text(
        "📢 *ANNOUNCEMENT GROUP SET!*\n\n"
        "Claim results will now be automatically "
        "announced in this group. 🎉",
        parse_mode="Markdown",
    )


# =========================================================
# /CLAIMS
# =========================================================

async def claims(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await admin_only(update):
        return

    if not claim_history:
        await update.message.reply_text(
            "📋 *CLAIM HISTORY*\n\n"
            "No prizes have been claimed yet.",
            parse_mode="Markdown",
        )
        return

    lines = [
        "📋 *CLAIM HISTORY*",
        "",
    ]

    for index, record in enumerate(
        claim_history,
        start=1,
    ):
        automatic_text = (
            " 🏁"
            if record.get(
                "automatic",
                False,
            )
            else ""
        )

        lines.append(
            f"{index}. "
            f"{record['username']} — "
            f"{record['prize']}"
            f"{automatic_text}"
        )

    lines.append("")

    lines.append(
        f"🎁 Total claimed: "
        f"*{len(claim_history)}/"
        f"{total_initial_prizes()}*"
    )

    lines.append("")

    lines.append(
        f"📦 Remaining global slots: "
        f"*{total_remaining_prizes()}*"
    )

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
    )


# =========================================================
# /RELOAD
# =========================================================

async def reload_prizes(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await admin_only(update):
        return

    global global_prizes

    global_prizes = (
        INITIAL_PRIZES.copy()
    )

    save_json(
        PRIZES_FILE,
        global_prizes,
    )

    await update.message.reply_text(
        "🔄 *PRIZES RELOADED!*\n\n"
        "All 15 prize slots have been restored globally. 🎡✨\n\n"
        "📋 Claim history has NOT been deleted.",
        parse_mode="Markdown",
    )


# =========================================================
# /CLEARCLAIMS
# =========================================================

async def clear_claims(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await admin_only(update):
        return

    global claim_history

    claim_history = []

    save_json(
        CLAIMS_FILE,
        claim_history,
    )

    await update.message.reply_text(
        "🧹 *CLAIM HISTORY CLEARED!*\n\n"
        "The prize inventory was not changed.",
        parse_mode="Markdown",
    )


# =========================================================
# MAIN
# =========================================================

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

    # ======================================
    # PARTICIPANT COMMANDS
    # ======================================

    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    application.add_handler(
        CommandHandler(
            "spin",
            spin,
        )
    )

    # ======================================
    # ADMIN COMMANDS
    # ======================================

    application.add_handler(
        CommandHandler(
            "grant",
            grant,
        )
    )

    application.add_handler(
        CommandHandler(
            "status",
            status,
        )
    )

    application.add_handler(
        CommandHandler(
            "revoke",
            revoke,
        )
    )

    application.add_handler(
        CommandHandler(
            "setgroup",
            set_group,
        )
    )

    application.add_handler(
        CommandHandler(
            "claims",
            claims,
        )
    )

    application.add_handler(
        CommandHandler(
            "reload",
            reload_prizes,
        )
    )

    application.add_handler(
        CommandHandler(
            "clearclaims",
            clear_claims,
        )
    )

    # ======================================
    # BUTTONS
    # ======================================

    application.add_handler(
        CallbackQueryHandler(
            button_handler,
        )
    )

    print(
        "Spin the Wheel bot is running..."
    )

    application.run_polling()


if __name__ == "__main__":
    main()
