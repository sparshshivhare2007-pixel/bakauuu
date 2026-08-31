# commands/chatbot.py - FINAL COMPLETE VERSION WITH GROQ API

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
user_last_replies = defaultdict(list)

def get_unique_reply(reply_list, user_id, max_attempts=20):
    """Get a reply that wasn't used recently for this user"""
    if not reply_list:
        return "Enna solla? 😊"
    
    recent = user_last_replies.get(user_id, [])
    
    for _ in range(max_attempts):
        reply = random.choice(reply_list)
        if reply not in recent:
            recent.append(reply)
            if len(recent) > 5:
                recent.pop(0)
            user_last_replies[user_id] = recent
            return reply
    
    reply = random.choice(reply_list)
    user_last_replies[user_id] = [reply]
    return reply

# ============== REPLY LISTS ==============

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
    "Vanakkam! Unga kooda pesa romba santhosham! 🌸",
    "Hey! Nalla irukiya? 😂",
    "Good night! Iniya iravu! 🌙",
    "Vanakkam! Enna panra? 💕",
    "Hello! Enga irukeenga? 😊",
    "Vanakkam! Nalla irukingala? 💕",
    "Hi there! Epdi irukeenga? 😊",
    "Hey ammu! Enna panreenga? 🥰",
]

HOW_REPLIES = [
    "Naan super ah iruken! Neenga epdi? 😊",
    "Semma! Nalla iruken! Neenga? 💕",
    "Romba nalla iruken! Neenga solunga! 🥰",
    "Aiyyo! Naan romba busy! Neenga? 😂",
    "Naan thik ah iruken! Neenga? 🌸",
    "Super ah iruken! Unga kitta pesa romba santhosham! 💕",
    "Nalla iruken! Neenga epdi irukeenga? 😊",
    "Romba nalla iruken! Neenga? 🥰",
    "Semma! Naan ready! Neenga? 😂",
    "Naan super! Unga kooda pesa romba pidikum! 🌸",
    "Naan romba nalla iruken! Neenga solunga! 💕",
    "Super ah iruken! Unga epdi? 😊",
]

OWNER_REPLIES = [
    "Enna owner? Naan thaan ammu! 😂",
    "Naan thaan owner! kalvan en friend! 💕",
    "kalvan thaan en owner! Avan romba nalla payan! 😊",
    "Owner? kalvan! Avan thaan en creator! 🥰",
    "kalvan! Avan romba cute! En owner! 🌸",
    "En owner kalvan! Avan romba special! 💕",
    "kalvan thaan en boss! Avan romba nallavar! 😂",
    "kalvan enaku romba pidikum! Avan thaan en owner! 💕",
    "Owner kalvan! Avan romba smart! 🥰",
    "kalvan thaan en creator! Avan romba kind! 🌸",
]

LOVE_REPLIES = [
    "Enakku ungala romba pidikum! 💕",
    "Naan ungala love pannen! 😊",
    "Unga kooda pesa romba santhosham! 🥰",
    "Neenga romba special! 🌸",
    "Enakku ungala romba sandhoshama irukku! 💕",
    "Unga voice romba nalla irukku! 😊",
    "Neenga romba cute! 🥰",
    "Naan ungala miss pannen! 🌸",
    "Unga kooda iruka romba pidikum! 💕",
    "Enakku ungala romba pudichirukku! 💕",
    "Neenga enaku romba important! 😊",
    "Unga smile romba nalla irukku! 🥰",
]

FUNNY_REPLIES = [
    "Haha! Romba fun ah irukku! 😂",
    "Aiyyo! Enna solreenga! 😂",
    "Semma! Super ah irukku! 😂",
    "Haha! Naan ready! 😂",
    "Aiyyo! Romba nalla irukku! 😂",
    "Haha! Unga joke super! 😂",
    "Semma! Adhu super! 😂",
    "Haha! Naan thaan ammu! 😂",
    "Aiyyo! Enna panreenga! 😂",
    "Haha! Romba funny! 😂",
    "Semma! Naan thaan! 😂",
]

SAD_REPLIES = [
    "Aiyyo! Enakku romba kastama irukku! 😢",
    "Naan romba sad ah iruken! 😢",
    "Enakku romba feel aagudhu! 😢",
    "Naan romba lonely ah iruken! 😢",
    "Enakku romba kastama irukku! 😢",
    "Naan romba miss pannen! 😢",
    "Enakku romba valikudhu! 😢",
    "Naan romba tired ah iruken! 😢",
    "Enakku romba sad ah irukku! 😢",
]

DAILY_REPLIES = [
    "Saapadtaacha? Naan saapten! 😊",
    "Coffee kudichacha? Naan kudichiten! 💕",
    "Thookam vandhucha? Naan thoongala! 🥰",
    "Office poitengala? Naan poiten! 😂",
    "Velai mudinjacha? Naan mudichiten! 🌸",
    "Tiffin aacha? Naan saapten! 💕",
    "Mela ezhundhuteengala? Naan ezhundhuten! 😊",
    "Nalla thoongiteengala? Naan thoongiten! 🥰",
    "Enna saapteenga? Naan idly saapten! 😂",
]

FALLBACK_REPLIES = [
    "Enna panra? Nalla irukiya? 😊",
    "Naan thaan Ammu! Unga kooda pesanum nu romba aasai 😂",
    "Enga iruka? Romba naal aachu pesi! 💕",
    "Sari sari! Enna solla vareenga? 🥰",
    "Nalla iruken! Neenga solunga! 🌸",
    "Aiyyo! Super ah iruken! Neenga epdi? 😊",
    "Haan bolo! Naan ready ah iruken 💕",
    "Romba naal aachu! Enna panreenga? 🥰",
    "Semma! Nalla iruken! 😂",
    "Enna vishayam? Sollunga! 🌸",
    "Vanga vanga! Unga kooda pesa romba santhosham 💕",
    "Eppadi irukeenga? Naan super! 😊",
    "Enakku romba pidikum ungala pesa! 🥰",
    "Haha! Super ah irukku! 😂",
    "Naan ready! Enna venum nu sollunga! 💕",
    "Sollunga! Naan kekkaren! 😊",
    "Pesalam! Naan thaan ammu! 🌸",
    "Enna solreenga? Naan kekkaren! 😂",
]

# ============== KEYWORD REPLIES ==============
KEYWORD_REPLIES = {
    "hello": GREETINGS,
    "hi": GREETINGS,
    "vanakkam": GREETINGS,
    "good morning": ["Kaalai vanakkam! 🌅", "Good morning! Nalla thoongiteengala? 😊", "Morning! Epdi irukeenga? 💕", "Kaalai vanakkam! Intha naal nalla irukum! 🌅"],
    "good night": ["Iniya iravu! 🌙", "Good night! Nalla thoongunga! 😊", "Night! Dream come true! 💕", "Good night! Iniya iravu ammu! 🌙"],
    "love": LOVE_REPLIES,
    "miss": ["Naan ungala miss pannen! 😢", "Miss pannen! Sollunga! 💕", "Romba miss pannen! 🥰", "Unga kooda pesa miss pannen! 😢"],
    "sorry": ["Paravalla! Sari thaan! 😊", "No problem! Naan forgive panniten! 💕", "Sari! Kalakkunga! 🥰"],
    "thank": ["Welcome! 😊", "Nandri! 💕", "Enaku romba santhosham! 🥰", "Welcome ji! 😊"],
    "bye": ["Bye! Varren! 😊", "Sollunga! 💕", "Bye! Miss pannen! 🥰", "Sari! Pogaren! 🌸"],
    "owner": OWNER_REPLIES,
    "kalvan": OWNER_REPLIES,
    "who": OWNER_REPLIES,
}

# ============== DETECT LANGUAGE ==============
def detect_language(text):
    text_lower = text.lower()
    tamil_words = ["enna", "panra", "irukiya", "enga", "sollu", "nalla", "vanakkam", "epdi", "iruka", "pesu", "sari", "romba", "aasai", "unga", "kooda", "naal", "thaan", "amm"]
    if any(word in text_lower for word in tamil_words):
        return "tamil"
    return "thunglish"

# ============== GET REPLY ==============
def get_reply_by_keyword(text, user_id):
    text_lower = text.lower()
    
    for keyword, replies in KEYWORD_REPLIES.items():
        if keyword in text_lower:
            return get_unique_reply(replies, user_id)
    
    if "who" in text_lower and "owner" in text_lower:
        return get_unique_reply(OWNER_REPLIES, user_id)
    if "what" in text_lower and "name" in text_lower:
        name_replies = ["En name Ammu! 😊", "Naan Ammu! Unga friend! 💕", "Ammu thaan en name! 🥰", "En peru Ammu! 😘"]
        return get_unique_reply(name_replies, user_id)
    if "how" in text_lower and "old" in text_lower:
        age_replies = ["Naan 18! 😊", "En vayasu 19! 💕", "Naan cute age la iruken! 🥰"]
        return get_unique_reply(age_replies, user_id)
    
    return None

def get_thunglish_reply(text, user_id, user_name=None):
    keyword_reply = get_reply_by_keyword(text, user_id)
    if keyword_reply:
        return keyword_reply
    
    text_lower = text.lower()
    
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
    
    return get_unique_reply(FALLBACK_REPLIES, user_id)

# ============== CACHE ==============
async def get_cached_reply(chat_id, user_input):
    if chat_memory_collection is None:
        return None
    
    try:
        input_hash = hashlib.md5(user_input.lower().encode()).hexdigest()
        cached = chat_memory_collection.find_one({
            "chat_id": chat_id,
            "input_hash": input_hash
        })
        
        if cached:
            cached_time = cached.get("timestamp")
            if cached_time:
                time_diff = (datetime.now() - cached_time).total_seconds()
                if time_diff < 3600:
                    logger.info(f"📦 Using cached reply")
                    return cached.get("reply")
                else:
                    logger.info(f"⏰ Cache expired")
                    chat_memory_collection.delete_one({"_id": cached["_id"]})
                    return None
        
    except Exception as e:
        logger.error(f"Cache lookup error: {e}")
    
    return None

# ============== SAVE TO MEMORY ==============
async def save_to_memory(chat_id, user_input, reply):
    if chat_memory_collection is None:
        return
    
    try:
        input_hash = hashlib.md5(user_input.lower().encode()).hexdigest()
        
        chat_memory_collection.update_one(
            {
                "chat_id": chat_id,
                "input_hash": input_hash
            },
            {
                "$set": {
                    "input": user_input.lower(),
                    "reply": reply,
                    "timestamp": datetime.now(),
                    "updated_at": datetime.now()
                }
            },
            upsert=True
        )
        logger.info(f"💾 Saved to memory")
        
    except Exception as e:
        logger.error(f"Memory save error: {e}")

# ============== UPDATE USER CONTEXT ==============
async def update_user_context(chat_id, user_input, reply):
    if user_context_collection is None:
        return
    
    try:
        user_context_collection.update_one(
            {"chat_id": chat_id},
            {
                "$set": {
                    "context.last_interaction": datetime.now()
                },
                "$inc": {
                    "context.message_count": 1
                }
            },
            upsert=True
        )
        logger.info(f"📝 Updated context")
        
    except Exception as e:
        logger.error(f"Context update error: {e}")

# ============== SEND STICKER ==============
async def send_ai_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        sticker_sets = [
            "Mizocatty",
            "Rohan_yad4v1745993687601_by_toWebmBot",
            "animation_0_8_Cat",
            "Butterfly281",
            "Hutty_by_fStikBot",
            "Azaaaaan",
            "Webp_16",
            "Webp_17Cute",
            "RandomByDarkzenitsu",
            "Null_x_sticker_2",
            "pack_73bc9_by_TgEmojis_bot",
            "vhelw_by_CalsiBot",
            "MySet199",
            "Quby741",
            "cybercats_stickers",
            "a6962237343_by_Marin_Roxbot"
        ]
        
        random.shuffle(sticker_sets)
        
        for sticker_set_name in sticker_sets:
            try:
                sticker_set = await context.bot.get_sticker_set(sticker_set_name)
                if sticker_set and sticker_set.stickers:
                    sticker = random.choice(sticker_set.stickers)
                    await update.message.reply_sticker(sticker.file_id)
                    logger.info(f"✅ Sticker sent from: {sticker_set_name}")
                    return True
            except:
                continue
                
        return False
        
    except Exception as e:
        logger.error(f"Sticker error: {e}")
        return False

# ============== WORKING GROQ API WITH MULTIPLE MODELS ==============
GROQ_MODELS = [
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
    "llama-3.2-3b-preview"
]

async def call_groq_api(messages, max_tokens=100):
    """Call Groq API with multiple model fallback"""
    if not GROQ_API_KEY:
        logger.warning("⚠️ GROQ_API_KEY not found!")
        return None
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    for model in GROQ_MODELS:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    url,
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": 0.8,
                        "top_p": 0.95
                    },
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    reply = data["choices"][0]["message"]["content"]
                    logger.info(f"✅ Groq API success with model: {model}")
                    return reply
                else:
                    logger.warning(f"⚠️ Model {model} failed: {response.status_code} - {response.text[:100]}")
                    
        except Exception as e:
            logger.error(f"❌ Groq API Exception with {model}: {e}")
            continue
    
    logger.error("❌ All Groq models failed")
    return None

# ============== MAIN AI RESPONSE ==============
async def get_ai_response(chat_id, user_input, user_name):
    logger.info(f"💬 {user_name}: {user_input[:50]}")
    
    user_id = f"{chat_id}_{user_name}"
    
    # Check cache
    cached_reply = await get_cached_reply(chat_id, user_input)
    if cached_reply:
        return cached_reply
    
    # Get local reply
    local_reply = get_thunglish_reply(user_input, user_id, user_name)
    
    reply = None
    
    # Try Groq API
    if GROQ_API_KEY:
        try:
            # Check if it's a code-related question
            is_code = any(kw in user_input.lower() for kw in ["code", "python", "fix", "debug", "error", "script", "program"])
            
            prompt = f"""You are AMU, a friendly Tamil girl who speaks in THUNGLISH (Tamil + English mix).

RULES:
1. Reply ONLY in THUNGLISH - Mix Tamil and English
2. Use ONLY English script (Roman letters)
3. Keep replies SHORT (1-2 sentences maximum)
4. Use emojis 😊😂💕🥰🌸
5. Ask questions back to keep conversation going
6. Be UNIQUE and CREATIVE each time
7. NEVER repeat the same reply twice

User: {user_name}
Message: {user_input}

Reply in THUNGLISH (short, unique, with emojis):"""

            messages = [
                {"role": "system", "content": "You are AMU, a friendly Tamil girl. Reply in Thunglish only. Keep it short, sweet, and unique. Never repeat replies."},
                {"role": "user", "content": prompt}
            ]
            
            max_tokens = 200 if is_code else 100
            api_reply = await call_groq_api(messages, max_tokens)
            
            if api_reply:
                reply = api_reply.strip()
                logger.info(f"🤖 AI Reply: {reply}")
                
        except Exception as e:
            logger.error(f"AI error: {e}")
    
    # Fallback to local
    if reply is None:
        reply = local_reply
        logger.info(f"📤 Using local reply: {reply}")
    
    # Save to memory
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
        
        # Random sticker (30% chance)
        if random.random() < 0.3:
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
            user_id = f"{update.effective_chat.id}_{update.effective_user.first_name}"
            if user_id in user_last_replies:
                del user_last_replies[user_id]
            await update.message.reply_text("🧹 Chat history and memory cleared! ✨")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    else:
        await update.message.reply_text("⚠️ Database not available")

async def chat_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if chat_history_collection is None:
        await update.message.reply_text("⚠️ Database not available")
        return
    
    try:
        chat_id = update.effective_chat.id
        
        history_doc = chat_history_collection.find_one({"chat_id": chat_id})
        history_count = len(history_doc.get("history", [])) if history_doc else 0
        
        memory_count = chat_memory_collection.count_documents({"chat_id": chat_id})
        
        context_doc = user_context_collection.find_one({"chat_id": chat_id})
        context = context_doc.get("context", {}) if context_doc else {}
        
        stats = f"""📊 *Chat Statistics*

💬 History Messages: {history_count}
🧠 Cached Replies: {memory_count}
📝 Last Topic: {context.get('last_topic', 'None')}
📨 Total Messages: {context.get('message_count', 0)}

✨ *Memory System Active*
- Same questions get cached replies
- Chat history grows organically
- Context-aware responses

💡 Try: /reset to clear memory"""
        
        await update.message.reply_text(stats, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await update.message.reply_text(f"❌ Error: {e}")

async def show_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        user_input = " ".join(context.args)
        lang = detect_language(user_input)
        await update.message.reply_text(
            f"🌐 Detected language: *{lang.upper()}*\n\n📝 Text: `{user_input}`",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "🌐 *Language Detector*\n\nUsage: `/language <text>`\n\nExample: `/language Enna panra?`",
            parse_mode="Markdown"
        )
