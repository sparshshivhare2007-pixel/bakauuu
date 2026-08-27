# chatbot.py
# Final BAKA Chatbot - Stickers, Emoji, Short Replies, Models

import os, random, httpx, logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction, ChatType, ParseMode
from dotenv import load_dotenv

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load API keys from .env
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
CODESTRAL_API_KEY = os.getenv("CODESTRAL_API_KEY")

# MongoDB chat history - Optional
try:
    from pymongo import MongoClient
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    logger.info(f"Connecting to MongoDB at: {MONGO_URI}")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    chatbot_collection = client.baka.chat_history
    logger.info("✅ MongoDB connected successfully!")
except Exception as e:
    logger.warning(f"⚠️ MongoDB not available: {e}")
    chatbot_collection = None

# === Fancy font style ===
def nezuko_style(text):
    return text.lower()

# === AI Models ===
MODELS = {
    "groq": {"url": "https://api.groq.com/openai/v1/chat/completions", "model": "llama3-70b-8192", "key": GROQ_API_KEY},
    "mistral": {"url": "https://api.mistral.ai/v1/chat/completions", "model": "mistral-large-latest", "key": MISTRAL_API_KEY},
    "codestral": {"url": "https://codestral.mistral.ai/v1/chat/completions", "model": "codestral-latest", "key": CODESTRAL_API_KEY}
}

STICKER_PACKS = [
    "https://t.me/addstickers/RandomByDarkzenitsu", 
    "https://t.me/addstickers/Null_x_sticker_2",
    "https://t.me/addstickers/pack_73bc9_by_TgEmojis_bot", 
    "https://t.me/addstickers/animation_0_8_Cat",
    "https://t.me/addstickers/vhelw_by_CalsiBot", 
    "https://t.me/addstickers/Rohan_yad4v1745993687601_by_toWebmBot",
    "https://t.me/addstickers/MySet199", 
    "https://t.me/addstickers/Quby741", 
    "https://t.me/addstickers/Animalsasthegtjtky_by_fStikBot",
    "https://t.me/addstickers/a6962237343_by_Marin_Roxbot", 
    "https://t.me/addstickers/cybercats_stickers"
]

# === Send random sticker ===
async def send_ai_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pack = random.choice(STICKER_PACKS)
        logger.info(f"🎨 Trying sticker pack: {pack}")
        s = await context.bot.get_sticker_set(pack)
        if s.stickers:
            sticker = random.choice(s.stickers).file_id
            await update.message.reply_sticker(sticker)
            logger.info("✅ Sticker sent")
        else:
            logger.warning("⚠️ No stickers found in pack")
    except Exception as e:
        logger.error(f"❌ Sticker error: {e}")

# === Call AI model API ===
async def call_model_api(provider, messages, max_tokens=50):
    conf = MODELS.get(provider)
    if not conf or not conf["key"]:
        logger.warning(f"⚠️ No API key found for {provider}")
        return None
    
    logger.info(f"📡 Calling {provider} API...")
    async with httpx.AsyncClient(timeout=25) as client:
        try:
            resp = await client.post(
                conf["url"],
                json={"model": conf["model"], "messages": messages, "max_tokens": max_tokens},
                headers={"Authorization": f"Bearer {conf['key']}"}
            )
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                logger.info(f"✅ API response: {content[:50]}...")
                return content
            else:
                logger.error(f"❌ API Error: {resp.status_code} - {resp.text[:200]}")
                return None
        except Exception as e:
            logger.error(f"❌ API Exception: {e}")
            return None

# === Generate AI response ===
async def get_ai_response(chat_id, user_input, user_name, model="mistral"):
    logger.info(f"💬 Getting response for: {user_name} | Input: {user_input[:30]}...")
    
    is_code = any(k in user_input.lower() for k in ["code", "python", "fix", "debug"])
    active_model = "codestral" if is_code else model
    tokens = 4096 if is_code else 50
    
    logger.info(f"🤖 Model: {active_model} | Code: {is_code}")

    prompt = f"You are AMU AI, a cute sassy Hinglish girl. Reply in 1 short sentence only. User: {user_name}"

    # Get history if MongoDB available
    history = []
    if chatbot_collection is not None:
        try:
            doc = chatbot_collection.find_one({"chat_id": chat_id}) or {}
            history = doc.get("history", [])
            logger.info(f"📚 Found {len(history)} history entries")
        except Exception as e:
            logger.error(f"❌ History fetch error: {e}")

    msgs = [{"role": "system", "content": prompt}] + history[-6:] + [{"role": "user", "content": user_input}]

    reply = await call_model_api(active_model, msgs, tokens)
    
    if reply is None:
        logger.warning("⚠️ No reply from API, using fallback")
        reply = "Main thik hu, tum kaise ho? 😊"

    # Save history if MongoDB available
    if chatbot_collection is not None:
        try:
            new_history = (history + [{"role":"user","content":user_input},{"role":"assistant","content":reply}])[-10:]
            chatbot_collection.update_one(
                {"chat_id": chat_id},
                {"$set": {"history": new_history}},
                upsert=True
            )
            logger.info("💾 History saved")
        except Exception as e:
            logger.error(f"❌ History save error: {e}")

    return reply, is_code

# === Automatic AI message handler ===
async def ai_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text or msg.text.startswith("/"):
        return

    logger.info("=" * 50)
    logger.info(f"📩 NEW MESSAGE")
    logger.info(f"📱 Chat ID: {update.effective_chat.id}")
    logger.info(f"👤 User: {msg.from_user.first_name} (@{msg.from_user.username or 'no username'})")
    logger.info(f"💬 Message: {msg.text}")
    logger.info(f"🏷️ Chat Type: {update.effective_chat.type}")

    # Check if bot should reply - ONLY "ammu"
    should_reply = False
    
    # Private chat - always reply
    if update.effective_chat.type == ChatType.PRIVATE:
        should_reply = True
        logger.info("✅ Private chat - will reply")
    
    # Reply to bot's message
    elif msg.reply_to_message and msg.reply_to_message.from_user.id == context.bot.id:
        should_reply = True
        logger.info("✅ Reply to bot - will reply")
    
    # Message contains "ammu"
    elif "ammu" in msg.text.lower():
        should_reply = True
        logger.info("✅ Contains 'ammu' - will reply")
    
    # Message starts with "ammu"
    elif msg.text.lower().startswith("ammu"):
        should_reply = True
        logger.info("✅ Starts with 'ammu' - will reply")
    
    else:
        logger.info("⏭️ No trigger word found - not replying")
    
    if should_reply:
        logger.info("🤖 PROCESSING REPLY...")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        
        try:
            res, code = await get_ai_response(
                update.effective_chat.id, 
                msg.text, 
                msg.from_user.first_name
            )
            
            logger.info(f"📤 Response: {res}")
            logger.info(f"📝 Is code: {code}")
            
            # Send response
            if code:
                await msg.reply_text(res)
                logger.info("✅ Code response sent")
            else:
                styled = nezuko_style(res)
                await msg.reply_text(styled)
                logger.info(f"✅ Styled response sent: {styled}")
            
            # Send sticker 80% of the time
            if random.random() < 0.8:
                logger.info("🎨 Sending sticker...")
                await send_ai_sticker(update, context)
            else:
                logger.info("⏭️ Skipping sticker (random chance)")
                
        except Exception as e:
            logger.error(f"❌ Error in processing: {e}")
            await msg.reply_text("Oops! Kuch gadbad ho gayi 😅")
    else:
        logger.info("⏭️ Not replying to this message")

# === /ask command handler ===
async def ask_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💬 Please type something after /ask")
        return
    user_input = " ".join(context.args)
    logger.info(f"📩 Ask command: {user_input}")
    res, code = await get_ai_response(update.effective_chat.id, user_input, update.effective_user.first_name)
    await update.message.reply_text(res if code else nezuko_style(res))
