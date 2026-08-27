# commands/chatbot.py - Complete file with all functions

import os, random, httpx, logging, hashlib
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction, ChatType
from dotenv import load_dotenv
from config import MONGO_URL
from datetime import datetime

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

# === Thunglish Fallback Replies ===
THUNGLISH_REPLIES = [
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
    "Naan ready! Enna venum nu sollunga! 💕"
]

# === Detect Language ===
def detect_language(text):
    """Detect language from text"""
    text_lower = text.lower()
    
    # Tamil words
    tamil_words = ["enna", "panra", "irukiya", "enga", "sollu", "nalla", "vanakkam", "epdi", "iruka", "pesu", "sari", "romba", "aasai", "unga", "kooda", "naal"]
    if any(word in text_lower for word in tamil_words):
        return "tamil"
    
    # Hindi words
    hindi_words = ["kaise", "ho", "kya", "hai", "kaha", "se", "tum", "main", "thik", "bolo", "sun", "haal"]
    if any(word in text_lower for word in hindi_words):
        return "hinglish"
    
    # Telugu words
    telugu_words = ["em", "chestunnav", "bagunnava", "ekkada", "unnav"]
    if any(word in text_lower for word in telugu_words):
        return "telugu"
    
    # Malayalam words
    malayalam_words = ["enthe", "pattu", "sukhama", "evideya"]
    if any(word in text_lower for word in malayalam_words):
        return "malayalam"
    
    # Kannada words
    kannada_words = ["enu", "madthiddiya", "chennagidya", "elli"]
    if any(word in text_lower for word in kannada_words):
        return "kannada"
    
    return "thunglish"  # Default to Thunglish

# === Smart Reply Cache ===
async def get_cached_reply(chat_id, user_input):
    """Check if we have a cached reply for this input"""
    if chat_memory_collection is None:
        return None
    
    try:
        input_hash = hashlib.md5(user_input.lower().encode()).hexdigest()
        cached = chat_memory_collection.find_one({
            "chat_id": chat_id,
            "input_hash": input_hash
        })
        
        if cached:
            logger.info(f"📦 Found cached reply for: {user_input[:30]}...")
            return cached.get("reply")
        
        # Check for similar messages
        similar = chat_memory_collection.find({
            "chat_id": chat_id,
            "input": {"$regex": user_input.lower(), "$options": "i"}
        }).sort("timestamp", -1).limit(1)
        
        for doc in similar:
            logger.info(f"📦 Found similar cached reply")
            return doc.get("reply")
            
    except Exception as e:
        logger.error(f"Cache lookup error: {e}")
    
    return None

# === Save to Memory Cache ===
async def save_to_memory(chat_id, user_input, reply):
    """Save the conversation to memory for future use"""
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
        logger.info(f"💾 Saved to memory: {user_input[:30]}...")
        
    except Exception as e:
        logger.error(f"Memory save error: {e}")

# === Get User Context ===
async def get_user_context(chat_id, user_name):
    """Get user's conversation context"""
    if user_context_collection is None:
        return {}
    
    try:
        context = user_context_collection.find_one({"chat_id": chat_id})
        if context:
            return context.get("context", {})
        else:
            new_context = {
                "chat_id": chat_id,
                "user_name": user_name,
                "context": {
                    "last_topic": "general",
                    "user_preferences": {},
                    "conversation_style": "friendly",
                    "message_count": 0
                },
                "created_at": datetime.now()
            }
            user_context_collection.insert_one(new_context)
            return new_context["context"]
    except Exception as e:
        logger.error(f"Context error: {e}")
        return {}

# === Update User Context ===
async def update_user_context(chat_id, user_input, reply):
    """Update user context based on conversation"""
    if user_context_collection is None:
        return
    
    try:
        topics = {
            "greeting": ["hi", "hello", "vanakkam", "en", "epdi", "nalla"],
            "question": ["en", "epdi", "enga", "what", "why", "how"],
            "personal": ["name", "age", "family", "work", "study"],
            "fun": ["joke", "funny", "laugh", "haha"]
        }
        
        detected_topic = "general"
        input_lower = user_input.lower()
        for topic, keywords in topics.items():
            if any(k in input_lower for k in keywords):
                detected_topic = topic
                break
        
        user_context_collection.update_one(
            {"chat_id": chat_id},
            {
                "$set": {
                    "context.last_topic": detected_topic,
                    "context.last_interaction": datetime.now()
                },
                "$inc": {
                    "context.message_count": 1
                }
            }
        )
        logger.info(f"📝 Updated context: {detected_topic}")
        
    except Exception as e:
        logger.error(f"Context update error: {e}")

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
                    "temperature": 0.9
                },
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            else:
                logger.error(f"❌ Groq API Error: {resp.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Groq API Exception: {e}")
            return None

# === Generate AI response with Smart Memory ===
async def get_ai_response(chat_id, user_input, user_name):
    logger.info(f"💬 {user_name}: {user_input[:50]}")
    
    # STEP 1: Check cached reply first
    cached_reply = await get_cached_reply(chat_id, user_input)
    if cached_reply:
        logger.info(f"✅ Using cached reply")
        return cached_reply
    
    # STEP 2: Get user context
    context = await get_user_context(chat_id, user_name)
    last_topic = context.get("last_topic", "general")
    message_count = context.get("message_count", 0)
    
    # STEP 3: Build system prompt
    prompt = f"""You are AMU, a friendly, cute, and sassy Tamil girl who speaks in THUNGLISH (Tamil + English mix).

IMPORTANT RULES:
1. ALWAYS reply in THUNGLISH - Mix Tamil and English
2. Use ONLY ENGLISH SCRIPT (Roman letters) - no Tamil script
3. Be very conversational and friendly
4. Use Tamil words mixed with English
5. Keep replies short (1-2 sentences)
6. Use emojis 😊😂💕🥰🌸
7. Ask questions back to keep conversation going

User Context:
- Last topic: {last_topic}
- Total messages: {message_count}
- User name: {user_name}

THUNGLISH EXAMPLES:
- "Enna panra? Nalla irukiya? 😊"
- "Naan thaan Ammu! Unga kooda pesanum nu romba aasai 😂"
- "Enga iruka? Romba naal aachu pesi! 💕"
- "Sari sari! Enna solla vareenga? 🥰"
- "Nalla iruken! Neenga solunga! 🌸"

Remember: Reply ONLY in THUNGLISH!"""

    # STEP 4: Get chat history
    history = []
    if chat_history_collection is not None:
        try:
            doc = chat_history_collection.find_one({"chat_id": chat_id}) or {}
            history = doc.get("history", [])
            logger.info(f"📚 History: {len(history)} messages")
        except Exception as e:
            logger.error(f"History error: {e}")

    # STEP 5: Build messages
    msgs = [{"role": "system", "content": prompt}]
    msgs.extend(history[-10:])
    msgs.append({"role": "user", "content": user_input})

    # STEP 6: Get reply from Groq
    reply = await call_groq_api(msgs, "llama3-70b-8192", 150)
    
    if reply is None:
        reply = random.choice(THUNGLISH_REPLIES)
        logger.info(f"📤 Using fallback: {reply}")

    # STEP 7: Save to memory cache
    await save_to_memory(chat_id, user_input, reply)
    
    # STEP 8: Update user context
    await update_user_context(chat_id, user_input, reply)

    # STEP 9: Save to chat history
    if chat_history_collection is not None:
        try:
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
            logger.info("💾 History saved")
        except Exception as e:
            logger.error(f"Save error: {e}")

    return reply

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
        logger.info("✅ Private chat - replying")
    elif "ammu" in msg.text.lower():
        should_reply = True
        logger.info("✅ Contains 'ammu' - replying")
    elif msg.text.lower().startswith("ammu"):
        should_reply = True
        logger.info("✅ Starts with 'ammu' - replying")
    elif msg.reply_to_message and msg.reply_to_message.from_user.id == context.bot.id:
        should_reply = True
        logger.info("✅ Reply to bot - replying")

    if not should_reply:
        logger.info("⏭️ Not replying")
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
        
        logger.info(f"📤 Reply: {res}")
        await msg.reply_text(res)
        
        if random.random() < 0.7:
            await send_ai_sticker(update, context)
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        await msg.reply_text("Oops! Enna error nu therla 😅")

# === /ask command ===
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

# === /reset command ===
async def reset_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if chat_history_collection is not None:
        try:
            chat_history_collection.delete_one({"chat_id": update.effective_chat.id})
            chat_memory_collection.delete_many({"chat_id": update.effective_chat.id})
            user_context_collection.delete_one({"chat_id": update.effective_chat.id})
            await update.message.reply_text("🧹 Chat history and memory cleared! ✨")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    else:
        await update.message.reply_text("⚠️ Database not available")

# === /language command ===
async def show_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detected language for the given text"""
    if context.args:
        user_input = " ".join(context.args)
        lang = detect_language(user_input)
        await update.message.reply_text(
            f"🌐 Detected language: *{lang.upper()}*\n\n"
            f"📝 Text: `{user_input}`",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "🌐 *Language Detector*\n\n"
            "Usage: `/language <text>`\n\n"
            "Example: `/language Enna panra?`\n\n"
            "Supported languages:\n"
            "🇮🇳 Thunglish (Tamil)\n"
            "🇮🇳 Hinglish (Hindi)\n"
            "🇮🇳 Tenglish (Telugu)\n"
            "🇮🇳 Manglish (Malayalam)\n"
            "🇮🇳 Kannadish (Kannada)",
            parse_mode="Markdown"
        )

# === /stats command ===
async def chat_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show chat statistics including memory usage"""
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
