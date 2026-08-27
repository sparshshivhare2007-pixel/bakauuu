# commands/admin.py
# Final Admin + Sudo System for BAKA Bot

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from database.db import get_user, users_col

OWNER_ID = 8172258194

# ===== SUDO SYSTEM (runtime) =====
SUDO_USERS = set()

def is_sudo(user_id: int):
    return user_id == OWNER_ID or user_id in SUDO_USERS

# ===== TARGET RESOLVER =====
async def get_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user

    if len(context.args) >= 2:
        target = context.args[1]

        # @username
        if target.startswith("@"):
            try:
                chat = await context.bot.get_chat(target)
                return chat
            except:
                return None

        # user id
        try:
            uid = int(target)
            class DummyUser:
                def __init__(self, id):
                    self.id = id
                    self.first_name = f"User_{id}"
                    self.name = f"User_{id}"
            return DummyUser(uid)
        except:
            return None

    return None

# ===== /transfer =====
async def transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_sudo(user.id):
        return await update.message.reply_text("❌ Only owner or sudo can use this.")

    if len(context.args) < 1:
        return await update.message.reply_text("⚠️ Usage: /transfer <amount> <reply/@user/id>")

    try:
        amount = int(context.args[0])
    except:
        return await update.message.reply_text("❌ Invalid amount.")

    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text("❌ User not found.")

    get_user(target)
    users_col.update_one(
        {"id": target.id},
        {"$inc": {"bal": amount}},
        upsert=True
    )

    name = getattr(target, "first_name", "User")
    await update.message.reply_text(f"✅ {name} ko ${amount} coins add kar diye!")

# ===== /remove =====
async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_sudo(user.id):
        return await update.message.reply_text("❌ Only owner or sudo can use this.")

    if len(context.args) < 1:
        return await update.message.reply_text("⚠️ Usage: /remove <amount> <reply/@user/id>")

    try:
        amount = int(context.args[0])
    except:
        return await update.message.reply_text("❌ Invalid amount.")

    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text("❌ User not found.")

    users_col.update_one(
        {"id": target.id},
        {"$inc": {"bal": -amount}},
        upsert=True
    )

    name = getattr(target, "first_name", "User")
    await update.message.reply_text(f"✅ {name} se ${amount} coins remove kar diye!")

# ===== /addsudo =====
async def addsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != OWNER_ID:
        return await update.message.reply_text("❌ Only owner can add sudo.")

    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text("❌ User not found.")

    SUDO_USERS.add(target.id)
    name = getattr(target, "first_name", "User")
    await update.message.reply_text(f"✅ {name} added as sudo.")

# ===== /rmsudo =====
async def rmsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != OWNER_ID:
        return await update.message.reply_text("❌ Only owner can remove sudo.")

    target = await get_target_user(update, context)
    if not target:
        return await update.message.reply_text("❌ User not found.")

    SUDO_USERS.discard(target.id)
    name = getattr(target, "first_name", "User")
    await update.message.reply_text(f"✅ {name} removed from sudo.")

# ===== REGISTER =====
def register_admin_commands(app):
    app.add_handler(CommandHandler("transfer", transfer))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("addsudo", addsudo))
    app.add_handler(CommandHandler("rmsudo", rmsudo))
