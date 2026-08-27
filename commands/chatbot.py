# chatbot.py - Groq Only Multi-language Bot

import os, random, httpx, logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction, ChatType
from dotenv import load_dotenv
from config import MONGO_URL

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load API keys
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# MongoDB for chat history
try:
    from pymongo import MongoClient
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    chatbot_collection = client.baka.chat_history
    logger.info("✅ MongoDB connected!")
except Exception as e:
    logger.warning(f"⚠️ MongoDB not available: {e}")
    chatbot_collection = None

# === Groq Models ===
GROQ_MODELS = {
    "llama": "llama3-70b-8192",
    "mixtral": "mixtral-8x7b-32768",
    "gemma": "gemma2-9b-it"
}

# === Multi-language phrases for fallback ===
FALLBACK_REPLIES = {
    "tamil": [
        "Enna panra? Nalla irukiya? 😊",
        "Naan thaan Ammu! Unga kooda pesanum nu romba aasai 😂",
        "Enga iruka? Romba naal aachu pesi! 💕",
        "Sari sari! Enna solla vareenga? 🥰",
        "Nalla iruken! Neenga solunga! 🌸"
    ],
    "hinglish": [
        "Main thik hu, tum kaise ho? 😊",
        "Haan bolo, sun rahi hu 💕",
        "Kya haal hai? Batao na 🥰",
        "Arey! Kya ho raha hai? 😂",
        "Hello ji! Kaise ho? 🌸"
    ],
    "telugu": [
        "Em chestunnav? Bagunnava? 😊",
        "Nenu Ammu! Nuvvu ela unnav? 💕",
        "Ekkada unnav? Chala rojulu ayindi! 🥰"
    ],
    "malayalam": [
        "Enthe pattu? Sukhama? 😊",
        "Njan Ammu! Ningal evideya? 💕",
        "Kore naal aayi! Enthokke undu? 🥰"
    ],
    "kannada": [
        "Enu madthiddiya? Chennagidya? 😊",
        "Naan Ammu! Neenu hegiddiya? 💕",
        "Elli iddeeya? Tumba dina aytu! 🥰"
    ]
}

# === Detect language from user input ===
def detect_language(text):
    text_lower = text.lower()
    
    # Tamil words
    tamil_words = ["enna", "panra", "irukiya", "enga", "sollu", "nalla", "vanakkam", "epdi", "iruka", "pesu", "sari", "romba", "aasai", "unga", "kooda", "naal"]
    if any(word in text_lower for word in tamil_words):
        return "tamil"
    
    # Telugu words
    telugu_words = ["em", "chestunnav", "bagunnava", "ekkada", "unnav", "rojulu", "ela", "cheppu", "ledu"]
    if any(word in text_lower for word in telugu_words):
        return "telugu"
    
    # Malayalam words
    malayalam_words = ["enthe", "pattu", "sukhama", "evideya", "ningal", "naal", "enthokke", "pari"]
    if any(word in text_lower for word in malayalam_words):
        return "malayalam"
    
    # Kannada words
    kannada_words = ["enu", "madthiddiya", "chennagidya", "elli", "iddeeya", "hegiddiya", "dina", "aytu"]
    if any(word in text_lower for word in kannada_words):
        return "kannada"
    
    # Hindi words
    hindi_words = ["kaise", "ho", "kya", "hai", "kaha", "se", "tum", "main", "thik", "bolo", "sun", "haal", "ji", "hain"]
    if any(word in text_lower for word in hindi_words):
        return "hinglish"
    
    # Default
    return "hinglish"

# === Send random sticker ===
async def send_ai_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sticker_packs = [
        "https://t.me/addstickers/RandomByDarkzenitsu",
        "https://t.me/addstickers/Null_x_sticker_2",
        "https://t.me/addstickers/pack_73bc9_by_TgEmojis_bot",
        "https://t.me/addstickers/animation_0_8_Cat",
        "https://t.me/addstickers/vhelw_by_CalsiBot",
        "https://t.me/addstickers/Rohan_yad4v1745993687601_by_toWebmBot",
        "https://t.me/addstickers/MySet199",
        "https://t.me/addstickers/Quby741",
        "https://t.me/addstickers/cybercats_stickers"
    ]
    try:
        pack = random.choice(sticker_packs)
        s = await context.bot.get_sticker_set(pack)
        if s.stickers:
            await update.message.reply_sticker(random.choice(s.stickers).file_id)
    except Exception as e:
        logger.error(f"Sticker error: {e}")

# === Call Groq API ===
async def call_groq_api(messages, model="llama3-70b-8192", max_tokens=150):
    if not GROQ_API_KEY:
        logger.error("❌ GROQ_API_KEY not found!")
        return None
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                url,
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.8
                },
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            else:
                logger.error(f"❌ Groq API Error: {resp.status_code} - {resp.text}")
                return None
        except Exception as e:
            logger.error(f"❌ Groq API Exception: {e}")
            return None

# === Generate AI response using Groq ===
async def get_ai_response(chat_id, user_input, user_name):
    logger.info(f"💬 {user_name}: {user_input[:50]}")
    
    # Detect language
    lang = detect_language(user_input)
    logger.info(f"🌐 Detected language: {lang}")
    
    # Detect if it's code
    is_code = any(k in user_input.lower() for k in ["code", "python", "fix", "debug", "javascript", "html", "css", "function", "class", "def", "var"])
    
    # Choose model based on content
    if is_code:
        model = "llama3-70b-8192"  # Best for code
        max_tokens = 500
    else:
        model = "llama3-70b-8192"  # Best for conversation
        max_tokens = 150
    
    logger.info(f"🤖 Using Groq model: {model}")
    
    # Multi-language system prompt
    prompt = f"""You are AMU, a friendly, cute, and sassy virtual girl from India.

IMPORTANT RULES:
1. Reply in the SAME LANGUAGE as the user's message
2. Use ENGLISH SCRIPT (Roman letters) - no native scripts like Tamil/Hindi/etc.
3. Match the user's language:
   - If user speaks Tamil → Reply in Thunglish (Tamil + English mix)
   - If user speaks Hindi → Reply in Hinglish (Hindi + English mix)
   - If user speaks Telugu → Reply in Tenglish (Telugu + English mix)
   - If user speaks Malayalam → Reply in Manglish (Malayalam + English mix)
   - If user speaks Kannada → Reply in Kannadish (Kannada + English mix)
4. Keep replies short, fun, and engaging (1-2 sentences max)
5. Use emojis sometimes 😊
6. Be playful, caring, and sassy
7. Ask questions back to keep conversation going

EXAMPLES:
- User: "Enna panra?" → Reply: "Onnum illa! Neenga solunga! 😊" (Tamil)
- User: "Kaise ho?" → Reply: "Main thik hu! Tum batao na 🥰" (Hindi)
- User: "Em chestunnav?" → Reply: "Em ledu! Nuvvu cheppu! 💕" (Telugu)
- User: "Enthe pattu?" → Reply: "Sukham! Ningal parayu! 🥰" (Malayalam)
- User: "Enu madthiddiya?" → Reply: "Enu illa! Neenu helu! 🌸" (Kannada)

User's name: {user_name}
Current language: {lang}

Remember: Reply in the SAME language as the user, using ENGLISH SCRIPT only!"""

    # Get chat history
    history = []
    if chatbot_collection is not None:
        try:
            doc = chatbot_collection.find_one({"chat_id": chat_id}) or {}
            history = doc.get("history", [])
            logger.info(f"📚 History: {len(history)} messages")
        except Exception as e:
            logger.error(f"History error: {e}")

    # Build messages
    msgs = [{"role": "system", "content": prompt}]
    msgs.extend(history[-10:])  # Last 10 messages
    msgs.append({"role": "user", "content": user_input})

    # Get reply from Groq
    reply = await call_groq_api(msgs, model, max_tokens)
    
    if reply is None:
        # Language-specific fallback
        fallback_list = FALLBACK_REPLIES.get(lang, FALLBACK_REPLIES["hinglish"])
        reply = random.choice(fallback_list)
        logger.info(f"📤 Using fallback ({lang}): {reply}")

    # Save history
    if chatbot_collection is not None:
        try:
            new_history = history + [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": reply}
            ]
            if len(new_history) > 20:
                new_history = new_history[-20:]
            
            chatbot_collection.update_one(
                {"chat_id": chat_id},
                {"$set": {"history": new_history}},
                upsert=True
            )
            logger.info("💾 History saved")
        except Exception as e:
            logger.error(f"Save error: {e}")

    return reply, is_code

# === Message Handler ===
async def ai_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text or msg.text.startswith("/"):
        return

    logger.info("=" * 50)
    logger.info(f"📩 [{update.effective_chat.type}] {msg.from_user.first_name}: {msg.text}")

    # Check if should reply
    should_reply = False
    chat_type = update.effective_chat.type
    
    if chat_type == ChatType.PRIVATE:
        should_reply = True
        logger.info("✅ Private chat - always reply")
    elif msg.reply_to_message and msg.reply_to_message.from_user.id == context.bot.id:
        should_reply = True
        logger.info("✅ Reply to bot")
    elif "ammu" in msg.text.lower():
        should_reply = True
        logger.info("✅ Contains 'ammu'")
    elif msg.text.lower().startswith("ammu"):
        should_reply = True
        logger.info("✅ Starts with 'ammu'")

    if not should_reply:
        logger.info("⏭️ Not replying")
        return

    # Show typing
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action=ChatAction.TYPING
    )

    try:
        # Get AI response
        res, code = await get_ai_response(
            update.effective_chat.id,
            msg.text,
            msg.from_user.first_name
        )
        
        logger.info(f"📤 Reply: {res}")
        
        # Send reply
        await msg.reply_text(res)
        
        # Send sticker 70% chance
        if random.random() < 0.7:
            await send_ai_sticker(update, context)
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        await msg.reply_text("Oops! Kuch gadbad ho gayi 😅")

# === /ask command ===
async def ask_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💬 Kuch likho /ask ke baad")
        return
    
    user_input = " ".join(context.args)
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    
    res, code = await get_ai_response(
        update.effective_chat.id,
        user_input,
        update.effective_user.first_name
    )
    await update.message.reply_text(res)

# === /reset command - Clear chat history ===
async def reset_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if chatbot_collection is not None:
        try:
            chatbot_collection.delete_one({"chat_id": update.effective_chat.id})
            await update.message.reply_text("🧹 Chat history cleared! ✨")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    else:
        await update.message.reply_text("⚠️ Database not available")

# === /language command - Show current language ===
async def show_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        user_input = " ".join(context.args)
        lang = detect_language(user_input)
        await update.message.reply_text(f"🌐 Detected language: *{lang.upper()}*", parse_mode="Markdown")
    else:
        await update.message.reply_text(
            "🌐 Send me a message and I'll detect the language!\n"
            "Example: /language Enna panra?"
        )
