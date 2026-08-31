# commands/chatbot.py - FIXED RANDOMIZATION VERSION

import os, random, httpx, logging, hashlib
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction, ChatType
from dotenv import load_dotenv
from config import MONGO_URL
from datetime import datetime
from collections import defaultdict

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# MongoDB setup
try:
    from pymongo import MongoClient
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client.baka
    chat_history_collection = db.chat_history
    chat_memory_collection = db.chat_memory
    user_context_collection = db.user_context
    logger.info("✅ MongoDB connected!")
except Exception as e:
    logger.warning(f"⚠️ MongoDB not available: {e}")
    chat_history_collection = None
    chat_memory_collection = None
    user_context_collection = None

# ============== TRACKER FOR LAST REPLIES (Prevents repetition) ==============
user_last_replies = defaultdict(list)  # Stores last 5 replies per user

def get_unique_reply(reply_list, user_id, max_attempts=20):
    """Get a reply that wasn't used recently for this user"""
    if not reply_list:
        return "Enna solla? 😊"
    
    # Get user's recent replies
    recent = user_last_replies.get(user_id, [])
    
    # Try to find a unique reply
    for _ in range(max_attempts):
        reply = random.choice(reply_list)
        if reply not in recent:
            # Update recent list
            recent.append(reply)
            if len(recent) > 5:  # Keep last 5
                recent.pop(0)
            user_last_replies[user_id] = recent
            return reply
    
    # If all are recent, force a new one
    reply = random.choice(reply_list)
    user_last_replies[user_id] = [reply]  # Reset
    return reply

# ============== EXPANDED REPLIES (500+ each) ==============

GREETINGS = [
    "Vanakkam! Epdi irukeenga? 😊",
    "Hello! Nalla irukiya? 💕",
    "Hi! Enna panreenga? 🥰",
    "Vanakkam! Romba naal aachu! 🌸",
    "Hey! Epdi irukeenga? 😂",
    "Good morning! Kaalai vanakkam! 🌅",
    "Good evening! Mala vanakkam! 🌆",
    "Vanakkam ammu! Naan ready! 💕",
    "Hello ji! Epdi irukeenga? 😊",
    "Hi ammu! Enna vishayam? 🥰",
    # ... add more here (I'm showing 10, but you have 100+ already)
]

# Similarly expand ALL other reply lists with more variations
# Add at least 50+ more to each category

# ============== IMPROVED KEYWORD REPLIES ==============
KEYWORD_REPLIES = {
    "hello": GREETINGS,
    "hi": GREETINGS,
    "vanakkam": GREETINGS,
    "good morning": [
        "Kaalai vanakkam! 🌅", 
        "Good morning! Nalla thoongiteengala? 😊", 
        "Morning! Epdi irukeenga? 💕",
        "Kaalai vanakkam! Intha naal nalla irukum! 🌅",
        "Good morning! Enna breakfast? 😊"
    ],
    # ... rest of your keyword replies
}

# ============== DETECT LANGUAGE ==============
def detect_language(text):
    text_lower = text.lower()
    tamil_words = ["enna", "panra", "irukiya", "enga", "sollu", "nalla", "vanakkam", "epdi", "iruka", "pesu", "sari", "romba", "aasai", "unga", "kooda", "naal", "thaan", "amm"]
    if any(word in text_lower for word in tamil_words):
        return "tamil"
    return "thunglish"

# ============== IMPROVED GET REPLY ==============
def get_reply_by_keyword(text, user_id):
    """Get unique reply based on keywords"""
    text_lower = text.lower()
    
    for keyword, replies in KEYWORD_REPLIES.items():
        if keyword in text_lower:
            return get_unique_reply(replies, user_id)
    
    # Handle specific questions
    if "who" in text_lower and "owner" in text_lower:
        return get_unique_reply(OWNER_REPLIES, user_id)
    if "what" in text_lower and "name" in text_lower:
        name_replies = ["En name Ammu! 😊", "Naan Ammu! Unga friend! 💕", "Ammu thaan en name! 🥰", "En peru Ammu! 😘", "Ammu nu sollunga! 💕"]
        return get_unique_reply(name_replies, user_id)
    
    return None

def get_thunglish_reply(text, user_id, user_name=None):
    """Get unique Thunglish reply"""
    
    # Check keyword first
    keyword_reply = get_reply_by_keyword(text, user_id)
    if keyword_reply:
        return keyword_reply
    
    text_lower = text.lower()
    
    # Check categories with unique replies
    if any(word in text_lower for word in ["vanakkam", "hello", "hi", "hey", "good morning", "good evening"]):
        return get_unique_reply(GREETINGS, user_id)
    
    if any(word in text_lower for word in ["epdi", "irukeenga", "how are", "nalla irukiya"]):
        return get_unique_reply(HOW_REPLIES, user_id)
    
    if "owner" in text_lower or "kalvan" in text_lower:
        return get_unique_reply(OWNER_REPLIES, user_id)
    
    if any(word in text_lower for word in ["love", "miss", "pidikum", "cute", "beautiful"]):
        return get_unique_reply(LOVE_REPLIES, user_id)
    
    if any(word in text_lower for word in ["funny", "joke", "meme", "haha", "😂"]):
        return get_unique_reply(FUNNY_REPLIES, user_id)
    
    if any(word in text_lower for word in ["sad", "feel", "kastam", "lonely", "alone", "cry"]):
        return get_unique_reply(SAD_REPLIES, user_id)
    
    if any(word in text_lower for word in ["saapad", "coffee", "thookam", "office", "velai", "tiffin", "sleep", "work"]):
        return get_unique_reply(DAILY_REPLIES, user_id)
    
    # Fallback with unique selection
    return get_unique_reply(FALLBACK_REPLIES, user_id)

# ============== CACHE WITH TIMESTAMP ==============
async def get_cached_reply(chat_id, user_input):
    """Get cached reply with time check"""
    if chat_memory_collection is None:
        return None
    
    try:
        input_hash = hashlib.md5(user_input.lower().encode()).hexdigest()
        cached = chat_memory_collection.find_one({
            "chat_id": chat_id,
            "input_hash": input_hash
        })
        
        if cached:
            # Check if cache is old (more than 1 hour)
            cached_time = cached.get("timestamp")
            if cached_time:
                time_diff = (datetime.now() - cached_time).total_seconds()
                if time_diff < 3600:  # 1 hour cache
                    logger.info(f"📦 Using cached reply (from {time_diff//60} mins ago)")
                    return cached.get("reply")
                else:
                    logger.info(f"⏰ Cache expired, generating new reply")
                    # Delete old cache
                    chat_memory_collection.delete_one({"_id": cached["_id"]})
                    return None
        
    except Exception as e:
        logger.error(f"Cache lookup error: {e}")
    
    return None

# ============== GROQ API WITH RETRY ==============
async def call_groq_api(messages, model="llama-3.1-70b-versatile", max_tokens=150, retries=2):
    """Call Groq API with retry"""
    if not GROQ_API_KEY:
        logger.warning("⚠️ GROQ_API_KEY not found!")
        return None
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    url,
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": 0.9,  # Higher temperature for more variety
                        "top_p": 0.95,
                    },
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    reply = data["choices"][0]["message"]["content"]
                    logger.info(f"✅ Groq API success (attempt {attempt+1})")
                    return reply
                else:
                    logger.error(f"❌ Groq API Error: {response.status_code} - {response.text[:100]}")
                    
        except Exception as e:
            logger.error(f"❌ Groq API Exception (attempt {attempt+1}): {e}")
            
    return None

# ============== MAIN AI RESPONSE ==============
async def get_ai_response(chat_id, user_input, user_name):
    logger.info(f"💬 {user_name}: {user_input[:50]}")
    
    user_id = f"{chat_id}_{user_name}"
    
    # Check cache (with time expiry)
    cached_reply = await get_cached_reply(chat_id, user_input)
    if cached_reply:
        return cached_reply
    
    # Get local reply first (with uniqueness)
    local_reply = get_thunglish_reply(user_input, user_id, user_name)
    
    reply = None
    
    # Try Groq API
    if GROQ_API_KEY:
        try:
            prompt = f"""You are AMU, a friendly, cute, and sassy Tamil girl who speaks in THUNGLISH (Tamil + English mix).

IMPORTANT RULES:
1. ALWAYS reply in THUNGLISH - Mix Tamil and English
2. Use ONLY ENGLISH SCRIPT (Roman letters)
3. Be very conversational and friendly
4. Use Tamil words mixed with English
5. Keep replies SHORT (1-2 sentences MAXIMUM)
6. Use emojis 😊😂💕🥰🌸
7. Ask questions back to keep conversation going
8. NEVER repeat the same reply twice
9. Be UNIQUE and CREATIVE each time

User: {user_name}
Message: {user_input}

Reply in THUNGLISH (short, unique, with emojis):"""

            messages = [{"role": "user", "content": prompt}]
            
            api_reply = await call_groq_api(messages, "llama-3.1-70b-versatile", 150)
            if api_reply:
                reply = api_reply.strip()
                logger.info(f"🤖 AI Reply: {reply}")
        except Exception as e:
            logger.error(f"AI error: {e}")
    
    # Fallback to local if AI failed
    if reply is None:
        reply = local_reply
        logger.info(f"📤 Using local reply: {reply}")
    
    # Save to cache
    await save_to_memory(chat_id, user_input, reply)
    await update_user_context(chat_id, user_input, reply)
    
    # Save history
    if chat_history_collection is not None:
        try:
            doc = chat_history_collection.find_one({"chat_id": chat_id}) or {}
            history = doc.get("history", [])
            
            new_history = history + [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": reply}
            ]
            if len(new_history) > 20:
                new_history = new_history[-20:]
            
            chat_history_collection.update_one(
                {"chat_id": chat_id},
                {"$set": {"history": new_history}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Save error: {e}")
    
    return reply

# ============== MESSAGE HANDLER ==============
async def ai_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text or msg.text.startswith("/"):
        return

    logger.info("=" * 50)
    logger.info(f"📩 [{update.effective_chat.type}] {msg.from_user.first_name}: {msg.text}")

    should_reply = False
    chat_type = update.effective_chat.type
    
    if chat_type == ChatType.PRIVATE:
        should_reply = True
    elif "ammu" in msg.text.lower() or msg.text.lower().startswith("ammu"):
        should_reply = True
    elif msg.reply_to_message and msg.reply_to_message.from_user.id == context.bot.id:
        should_reply = True

    if not should_reply:
        return

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action=ChatAction.TYPING
    )

    try:
        res = await get_ai_response(
            update.effective_chat.id,
            msg.text,
            msg.from_user.first_name
        )
        
        logger.info(f"📤 Final Reply: {res}")
        await msg.reply_text(res)
        
        # Random sticker (40% chance)
        if random.random() < 0.4:
            await send_ai_sticker(update, context)
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        await msg.reply_text("Oops! Enna error nu therla 😅")

# ============== COMMANDS ==============
async def ask_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💬 Enna venum nu sollunga /ask kooda")
        return
    
    user_input = " ".join(context.args)
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    
    res = await get_ai_response(
        update.effective_chat.id,
        user_input,
        update.effective_user.first_name
    )
    await update.message.reply_text(res)

async def reset_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if chat_history_collection is not None:
        try:
            chat_history_collection.delete_one({"chat_id": update.effective_chat.id})
            chat_memory_collection.delete_many({"chat_id": update.effective_chat.id})
            user_context_collection.delete_one({"chat_id": update.effective_chat.id})
            # Clear user's recent replies
            user_id = f"{update.effective_chat.id}_{update.effective_user.first_name}"
            if user_id in user_last_replies:
                del user_last_replies[user_id]
            await update.message.reply_text("🧹 Chat history and memory cleared! ✨")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    else:
        await update.message.reply_text("⚠️ Database not available")
