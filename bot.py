# ================== LOAD .env FIRST ==================
from dotenv import load_dotenv
load_dotenv()

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ================== LOGGING ==================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ================== LOAD CONFIG ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN not found")

# ================== IMPORT DATABASE ==================
from database.db import get_user

# ================== IMPORT COMMANDS ==================
from commands.economy import (
    bal, rob, kill, revive, protect, give,
    myrank, toprich, leaders,
    economy, open_economy, close_economy
)
from commands.game import register_game_commands
from commands.admin import register_admin_commands
from commands.logger import register_logger
from commands.broadcast import register_broadcast
from commands.chatbot import (
    ask_ai, 
    ai_message_handler, 
    reset_chat, 
    # show_language,
    chat_stats
)
from commands.couple import couple
from commands.shop import items, item, gift
from commands.quote import q
from commands.welcome import welcome
from commands.td import get_truth, get_dare
from commands.swagat import swagat, welcome_new_member
from commands.radhe import register_radhe

# Fun
from commands.fun import (
    slap, hug, punch, kiss, bite,
    crush, brain, id_cmd, love, stupid_meter
)

# ================== START IMAGE ==================
START_IMAGE_URL = "https://files.catbox.moe/49sy7j.jpg"

# ================== AUTO REGISTER ==================
async def auto_register_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        chat = update.effective_chat
        if user and chat and not user.is_bot:
            get_user(user, chat.id)
    except Exception as e:
        logging.error(f"Auto-register error: {e}")

# ================== /START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return await update.message.reply_text(
            "📩 Start me in private",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "💬 Open Private",
                    url=f"https://t.me/{context.bot.username}"
                )]
            ])
        )

    user = update.effective_user
    keyboard = [
        [
            InlineKeyboardButton("💬 Talk to Ammu", callback_data="talk_ammu"),
            InlineKeyboardButton("✨ kalvan", url="https://t.me/MR_KALVAN")
        ],
        [
            InlineKeyboardButton("➕ Add to Group",
                url=f"https://t.me/{context.bot.username}?startgroup=true"
            )
        ]
    ]

    await update.message.reply_photo(
        photo=START_IMAGE_URL,
        caption=f"✨ Hey *{user.first_name}*\n💌 I'm *𝗜'𝗠 🎼 𝝠 𝗠 𝗠 𝗨* - Your virtual friend!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================== BUTTON ==================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "talk_ammu":
        await query.message.reply_text("Haan ennu parada 💕")

# ================== AI HANDLER - GROQ + THUNGLISH + SMART MEMORY ==================
async def safe_ai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    AI Handler with:
    - Groq API
    - Thunglish (Tamil + English)
    - Smart Memory Cache
    - Private chat: Always reply
    - Group chat: Only if message contains 'ammu'
    - No typing loop
    """
    if not update.message or not update.message.text:
        return

    # Check if should reply
    should_reply = False
    chat_type = update.effective_chat.type
    
    # Private chat - always reply
    if chat_type == "private":
        should_reply = True
        logging.info(f"💬 Private chat: {update.message.text}")
    
    # Group chat - only if contains "ammu"
    elif "ammu" in update.message.text.lower():
        should_reply = True
        logging.info(f"💬 Group chat with 'ammu': {update.message.text}")
    
    # Reply to bot's message
    elif update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
        should_reply = True
        logging.info(f"💬 Reply to bot: {update.message.text}")

    if not should_reply:
        return

    # Call the AI handler from chatbot.py
    await ai_message_handler(update, context)

# ================== ERROR ==================
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Bot error: {context.error}")

# ================== MAIN ==================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # ---------- AUTO REGISTER (LOWEST PRIORITY) ----------
    app.add_handler(
        MessageHandler(filters.ALL, auto_register_handler),
        group=-1
    )

    # ---------- CORE ----------
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    # ---------- ECONOMY ----------
    app.add_handler(CommandHandler("bal", bal))
    app.add_handler(CommandHandler("rob", rob))
    app.add_handler(CommandHandler("kill", kill))
    app.add_handler(CommandHandler("revive", revive))
    app.add_handler(CommandHandler("protect", protect))
    app.add_handler(CommandHandler("give", give))
    app.add_handler(CommandHandler("myrank", myrank))
    app.add_handler(CommandHandler("toprich", toprich))
    app.add_handler(CommandHandler("leaders", leaders))
    app.add_handler(CommandHandler("economy", economy))
    app.add_handler(CommandHandler("open", open_economy))
    app.add_handler(CommandHandler("close", close_economy))

    # ---------- FUN ----------
    app.add_handler(CommandHandler("slap", slap))
    app.add_handler(CommandHandler("hug", hug))
    app.add_handler(CommandHandler("punch", punch))
    app.add_handler(CommandHandler("kiss", kiss))
    app.add_handler(CommandHandler("bite", bite))
    app.add_handler(CommandHandler("love", love))
    app.add_handler(CommandHandler("stupid_meter", stupid_meter))
    app.add_handler(CommandHandler("crush", crush))
    app.add_handler(CommandHandler("brain", brain))
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(CommandHandler("couple", couple))
    app.add_handler(CommandHandler("items", items))
    app.add_handler(CommandHandler("item", item))
    app.add_handler(CommandHandler("gift", gift))
    app.add_handler(CommandHandler("truth", get_truth))
    app.add_handler(CommandHandler("dare", get_dare))
    app.add_handler(CommandHandler("q", q))

    # ---------- WELCOME ----------
    app.add_handler(CommandHandler("swagat", swagat))
    app.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS,
        welcome_new_member
    ))
    app.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS,
        welcome
    ))

    # ---------- MODULE REGISTERS ----------
    register_game_commands(app)
    register_logger(app)
    register_broadcast(app)
    register_admin_commands(app)
    register_radhe(app)

    # ---------- AI COMMANDS (GROQ + THUNGLISH + SMART MEMORY) ----------
    app.add_handler(CommandHandler("ask", ask_ai))          # Ask anything
    app.add_handler(CommandHandler("reset", reset_chat))    # Clear chat history & memory
    # app.add_handler(CommandHandler("language", show_language)) # Detect language
    app.add_handler(CommandHandler("stats", chat_stats))    # Show chat statistics
    
    # ---------- AI MESSAGE HANDLER ----------
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, safe_ai_handler)
    )

    # ---------- ERROR ----------
    app.add_error_handler(error_handler)

    print("=" * 50)
    print("✅ Ammu Bot Online with Smart Memory!")
    print("=" * 50)
    print("🤖 AI Engine: Groq (Llama3-70b)")
    print("🌐 Language: Thunglish (Tamil + English)")
    print("🧠 Memory: Smart Cache System")
    print("📊 Features: Chat History, User Context, Cached Replies")
    print("💬 Trigger: 'ammu' in groups | Always reply in private")
    print("=" * 50)
    print("📝 Commands:")
    print("  /ask <question>  - Ask anything")
    print("  /reset           - Clear chat history & memory")
    print("  /language <text> - Detect language")
    print("  /stats           - Show chat statistics")
    print("=" * 50)
    
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
