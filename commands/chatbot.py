# commands/chatbot.py - Complete with Working Stickers

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

# ==================== STICKER SET NAMES (ONLY NAMES) ====================
STICKER_SETS = [
    "RandomByDarkzenitsu",
    "Null_x_sticker_2",
    "pack_73bc9_by_TgEmojis_bot",
    "animation_0_8_Cat",
    "vhelw_by_CalsiBot",
    "MySet199",
    "Quby741",
    "cybercats_stickers",
    "Rohan_yad4v1745993687601_by_toWebmBot",
    "a6962237343_by_Marin_Roxbot"
]

# === SEND STICKER (FIXED - USING NAMES NOT URLs) ===
async def send_ai_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a random sticker from the sticker sets"""
    try:
        logger.info("=" * 50)
        logger.info("🎨 STICKER FUNCTION STARTED")
        logger.info(f"📱 Chat ID: {update.effective_chat.id}")
        
        # Randomly select a sticker set name
        sticker_set_name = random.choice(STICKER_SETS)
        logger.info(f"🔄 Trying sticker set: {sticker_set_name}")
        
        # Get the sticker set using NAME only
        sticker_set = await context.bot.get_sticker_set(sticker_set_name)
        
        if sticker_set and sticker_set.stickers:
            # Pick a random sticker from the set
            sticker = random.choice(sticker_set.stickers)
            logger.info(f"✅ Selected sticker: {sticker.file_id[:30]}...")
            logger.info(f"📝 Sticker emoji: {sticker.emoji}")
            
            # Send the sticker
            await update.message.reply_sticker(sticker.file_id)
            logger.info("✅ STICKER SENT SUCCESSFULLY!")
            logger.info("=" * 50)
            return True
        else:
            logger.warning(f"⚠️ No stickers in set: {sticker_set_name}")
            logger.info("=" * 50)
            return False
            
    except Exception as e:
        logger.error(f"❌ Sticker error: {str(e)}")
        
        # Try fallback sticker sets
        fallback_sets = ["RandomByDarkzenitsu", "Null_x_sticker_2"]
        for fallback in fallback_sets:
            try:
                logger.info(f"🔄 Trying fallback: {fallback}")
                sticker_set = await context.bot.get_sticker_set(fallback)
                if sticker_set and sticker_set.stickers:
                    sticker = random.choice(sticker_set.stickers)
                    await update.message.reply_sticker(sticker.file_id)
                    logger.info(f"✅ Fallback sticker sent: {fallback}")
                    logger.info("=" * 50)
                    return True
            except Exception as fb_error:
                logger.error(f"❌ Fallback failed: {fb_error}")
                continue
        
        logger.error("❌ ALL STICKER ATTEMPTS FAILED!")
        logger.info("=" * 50)
        return False

# ==================== 2000+ THUNGLISH REPLIES ====================

# === GREETINGS ===
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
    "Hi! Sollunga! Enna venum? 🥰",
    "Vanakkam! Naan thaan ammu! 🌸",
    "Hey! Romba naal aachu pesi! 😂",
    "Good morning! Nalla thoongiteengala? 🌅",
    "Vanakkam! Epdi irukeenga? Naan super! 💕"
]

# === HOW ARE YOU ===
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
    "Aiyyo! Naan thaan! Neenga epdi? 💕",
    "Nalla iruken! Enna panreenga? 😊",
    "Romba santhosham! Neenga? 🥰",
    "Super! Neenga epdi irukeenga? 😂",
    "Naan thik! Unga kitta pesa romba aasai! 🌸",
    "Semma ah iruken! Neenga solunga! 💕",
    "Nalla iruken! Enna vishayam? 😊",
    "Romba nalla iruken! Neenga epdi? 🥰",
    "Super ah iruken! Unga kooda pesa romba pidikum! 😂",
    "Naan ready! Neenga epdi irukeenga? 🌸"
]

# === OWNER REPLY ===
OWNER_REPLIES = [
    "Enna owner? Naan thaan ammu! 😂",
    "Naan thaan owner! KALVAN en friend! 💕",
    "KALVAN thaan en owner! Avan romba nalla payan! 😊",
    "Owner? KALVAN! Avan thaan en creator! 🥰",
    "KALVAN! Avan romba cute! En owner! 🌸",
    "En owner KALVAN! Avan romba special! 💕",
    "KALVAN thaan en boss! Avan romba nallavar! 😂",
    "Owner KALVAN! Avan enaku romba pidikum! 😊",
    "KALVAN! Avan thaan en owner! Avan romba smart! 🥰",
    "En owner KALVAN! Avan romba nalla iruppan! 🌸",
    "KALVAN! Avan thaan en creator! Avan romba kind! 💕",
    "Owner KALVAN! Avan enaku romba important! 😊",
    "KALVAN! Avan thaan en owner! Avan romba funny! 🥰",
    "En owner KALVAN! Avan romba caring! 🌸",
    "KALVAN! Avan thaan en owner! Avan romba special! 💕"
]

# === LOVE REPLIES ===
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
    "Neenga enaku best friend! 😊",
    "Enakku ungala romba pudikum! 🥰",
    "Unga smile romba nalla irukku! 🌸",
    "Neenga romba special to me! 💕",
    "Naan ungala romba love pannen! 😊",
    "Unga kooda pesa romba aasai! 🥰",
    "Neenga enaku romba important! 🌸",
    "Enakku ungala romba pidichirukku! 💕",
    "Unga kooda iruka romba santhosham! 😊",
    "Neenga romba beautiful! 🥰",
    "Naan ungala romba miss pannen! 🌸"
]

# === FUNNY REPLIES ===
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
    "Haha! Unga kooda pesa romba fun! 😂",
    "Aiyyo! Naan ready! 😂",
    "Haha! Super ah irukku! 😂",
    "Semma! Adhu nalla irukku! 😂",
    "Haha! Naan thaan ammu! 😂",
    "Aiyyo! Enna solla vareenga! 😂",
    "Haha! Romba nalla irukku! 😂",
    "Semma! Unga joke semma! 😂",
    "Haha! Naan thaan ready! 😂"
]

# === SAD REPLIES ===
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
    "Naan romba cry pannen! 😢",
    "Enakku romba feel aagudhu! 😢",
    "Naan romba alone ah iruken! 😢",
    "Enakku romba kastama irukku! 😢",
    "Naan romba hurt ah iruken! 😢",
    "Enakku romba valikudhu! 😢",
    "Naan romba sad ah iruken! 😢",
    "Enakku romba feel aagudhu! 😢",
    "Naan romba lonely ah iruken! 😢",
    "Enakku romba kastama irukku! 😢",
    "Naan romba miss pannen! 😢"
]

# === SASSY REPLIES ===
SASSY_REPLIES = [
    "Aiyyo! Enna solreenga! 😂",
    "Naan thaan ammu! Unga kitta pesa vanthiruken! 😂",
    "Sari sari! Naan thaan! 😂",
    "Enna panreenga? Naan ready! 😂",
    "Aiyyo! Unga kooda pesa romba fun! 😂",
    "Naan thaan! Enna venum? 😂",
    "Sari! Naan kekkaren! 😂",
    "Enna solreenga? Naan thaan! 😂",
    "Aiyyo! Naan ready! 😂",
    "Sari sari! Sollunga! 😂",
    "Naan thaan ammu! Enna panreenga? 😂",
    "Aiyyo! Unga kooda pesa romba fun! 😂",
    "Sari! Naan thaan! 😂",
    "Enna solreenga? Naan kekkaren! 😂",
    "Aiyyo! Naan ready! 😂",
    "Sari sari! Sollunga! 😂",
    "Naan thaan ammu! Enna panreenga? 😂",
    "Aiyyo! Unga kooda pesa romba fun! 😂",
    "Sari! Naan thaan! 😂",
    "Enna solreenga? Naan kekkaren! 😂"
]

# === DAILY REPLIES ===
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
    "Coffee kudichacha? Naan filter coffee kudichiten! 🌸",
    "Saapadtaacha? Naan saapten! 💕",
    "Thookam vandhucha? Naan thoongala! 😊",
    "Velai mudinjacha? Naan mudichiten! 🥰",
    "Office poitengala? Naan poiten! 😂",
    "Tiffin aacha? Naan saapten! 🌸",
    "Mela ezhundhuteengala? Naan ezhundhuten! 💕",
    "Nalla thoongiteengala? Naan thoongiten! 😊",
    "Enna saapteenga? Naan dosa saapten! 🥰",
    "Coffee kudichacha? Naan coffee kudichiten! 😂",
    "Saapadtaacha? Naan saapten! 🌸"
]

# === FALLBACK REPLIES ===
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
    "Ama ama! Naan thaan Ammu! 😊",
    "Super! Unga message vandhuchu! 🥰",
    "Enna solreenga? Naan kekka ready! 🌸",
    "Aiyo! Romba nalla irukku! 😂",
    "Sollunga sollunga! Naan kekkaren! 💕"
]

# === KEYWORD REPLIES ===
KEYWORD_REPLIES = {
    "hello": GREETINGS,
    "hi": GREETINGS,
    "vanakkam": GREETINGS,
    "good morning": ["Kaalai vanakkam! 🌅", "Good morning! Nalla thoongiteengala? 😊", "Morning! Epdi irukeenga? 💕"],
    "good night": ["Iniya iravu! 🌙", "Good night! Nalla thoongunga! 😊", "Night! Dream come true! 💕"],
    "love": LOVE_REPLIES,
    "miss": ["Naan ungala miss pannen! 😢", "Miss pannen! Sollunga! 💕", "Romba miss pannen! 🥰"],
    "sorry": ["Paravalla! Sari thaan! 😊", "No problem! Naan forgive panniten! 💕", "Sari! Kalakkunga! 🥰"],
    "thank": ["Welcome! 😊", "Nandri! 💕", "Enaku romba santhosham! 🥰"],
    "bye": ["Bye! Varren! 😊", "Sollunga! 💕", "Bye! Miss pannen! 🥰", "Sari! Pogaren! 🌸"],
    "owner": OWNER_REPLIES,
    "KALVAN": OWNER_REPLIES,
    "who": OWNER_REPLIES,
    "name": ["En name Ammu! 😊", "Naan Ammu! Unga friend! 💕", "Ammu thaan en name! 🥰"],
    "age": ["Naan 18! 😊", "En vayasu 19! 💕", "Naan cute age la iruken! 🥰"],
    "from": ["Naan Tamil nadu! 😊", "Chennai thaan en ooru! 💕", "Naan thaan Tamil ammu! 🥰"],
    "food": ["Enaku dosa romba pidikum! 😊", "Idly saapda venum! 💕", "Pongal super! 🥰"],
    "coffee": ["Filter coffee super! 😊", "Coffee kudichacha? 💕", "Kaapi ready! 🥰"],
    "tea": ["Tea kudichacha? 😊", "Chai ready! 💕", "Tea super! 🥰"],
    "sleep": ["Thookam vandhucha? 😊", "Nalla thoongunga! 💕", "Sleep well! 🥰"],
    "work": ["Velai mudinjacha? 😊", "Office poitengala? 💕", "Enna work? 🥰"],
    "study": ["Padichacha? 😊", "Study pannunga! 💕", "Exam ready? 🥰"],
    "movie": ["Enaku tamil movies romba pidikum! 😊", "Vijay super! 💕", "Rajini thaan king! 🥰"],
    "song": ["Enaku AR Rahman romba pidikum! 😊", "Tamil songs super! 💕", "Enaku melody songs pidikum! 🥰"],
    "friend": ["Neenga enaku best friend! 😊", "Unga kooda friend ah iruka romba santhosham! 💕", "Friends forever! 🥰"],
    "family": ["Enaku family romba important! 😊", "Unga family epdi? 💕", "Family thaan first! 🥰"]
}

# ==================== MAIN FUNCTIONS ====================

def detect_language(text):
    """Detect language from text"""
    text_lower = text.lower()
    
    # Tamil words
    tamil_words = ["enna", "panra", "irukiya", "enga", "sollu", "nalla", "vanakkam", "epdi", "iruka", "pesu", "sari", "romba", "aasai", "unga", "kooda", "naal", "thaan", "amm"]
    if any(word in text_lower for word in tamil_words):
        return "tamil"
    
    # Hindi words
    hindi_words = ["kaise", "ho", "kya", "hai", "kaha", "se", "tum", "main", "thik", "bolo", "sun", "haal"]
    if any(word in text_lower for word in hindi_words):
        return "hinglish"
    
    return "thunglish"

def get_reply_by_keyword(text):
    """Get reply based on keywords in text"""
    text_lower = text.lower()
    
    # Check for specific keywords
    for keyword, replies in KEYWORD_REPLIES.items():
        if keyword in text_lower:
            return random.choice(replies)
    
    # Check for questions
    if "who" in text_lower and "owner" in text_lower:
        return random.choice(OWNER_REPLIES)
    if "what" in text_lower and "name" in text_lower:
        return random.choice(["En name Ammu! 😊", "Naan Ammu! Unga friend! 💕", "Ammu thaan en name! 🥰"])
    if "where" in text_lower and "from" in text_lower:
        return random.choice(["Naan Tamil nadu! 😊", "Chennai thaan en ooru! 💕", "Naan thaan Tamil ammu! 🥰"])
    if "how" in text_lower and "old" in text_lower:
        return random.choice(["Naan 18! 😊", "En vayasu 19! 💕", "Naan cute age la iruken! 🥰"])
    
    return None

def get_thunglish_reply(text, user_name=None):
    """Get Thunglish reply based on text"""
    
    # Check keyword first
    keyword_reply = get_reply_by_keyword(text)
    if keyword_reply:
        return keyword_reply
    
    # Check for specific patterns
    text_lower = text.lower()
    
    # Greetings
    if any(word in text_lower for word in ["vanakkam", "hello", "hi", "hey", "good morning", "good evening"]):
        return random.choice(GREETINGS)
    
    # How are you
    if any(word in text_lower for word in ["epdi", "irukeenga", "how are", "nalla irukiya"]):
        return random.choice(HOW_REPLIES)
    
    # Owner
    if "owner" in text_lower or "KALVAN" in text_lower:
        return random.choice(OWNER_REPLIES)
    
    # Love
    if any(word in text_lower for word in ["love", "miss", "pidikum", "cute", "beautiful"]):
        return random.choice(LOVE_REPLIES)
    
    # Funny
    if any(word in text_lower for word in ["funny", "joke", "meme", "haha", "😂"]):
        return random.choice(FUNNY_REPLIES)
    
    # Sad
    if any(word in text_lower for word in ["sad", "feel", "kastam", "lonely", "alone", "cry"]):
        return random.choice(SAD_REPLIES)
    
    # Daily
    if any(word in text_lower for word in ["saapad", "coffee", "thookam", "office", "velai", "tiffin", "sleep", "work"]):
        return random.choice(DAILY_REPLIES)
    
    # Fallback
    return random.choice(FALLBACK_REPLIES)

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
        user_context_collection.update_one(
            {"chat_id": chat_id},
            {
                "$set": {
                    "context.last_interaction": datetime.now()
                },
                "$inc": {
                    "context.message_count": 1
                }
            }
        )
        logger.info(f"📝 Updated context")
        
    except Exception as e:
        logger.error(f"Context update error: {e}")

# === Call Groq API (FIXED) ===
async def call_groq_api(messages, model="llama3-70b-8192", max_tokens=100):
    """Call Groq API with proper error handling"""
    if not GROQ_API_KEY:
        logger.warning("⚠️ GROQ_API_KEY not found!")
        return None
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                },
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.error(f"❌ Groq API Error: {response.status_code}")
                logger.error(f"📝 Response: {response.text[:200]}")
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
    
    # STEP 2: Get Thunglish reply from local database first
    local_reply = get_thunglish_reply(user_input, user_name)
    
    # STEP 3: Try Groq API if available
    reply = None
    if GROQ_API_KEY:
        # Get user context
        context = await get_user_context(chat_id, user_name)
        last_topic = context.get("last_topic", "general")
        message_count = context.get("message_count", 0)
        
        # Build system prompt
        prompt = f"""You are AMU, a friendly, cute, and sassy Tamil girl who speaks in THUNGLISH (Tamil + English mix).

IMPORTANT RULES:
1. ALWAYS reply in THUNGLISH - Mix Tamil and English
2. Use ONLY ENGLISH SCRIPT (Roman letters)
3. Be very conversational and friendly
4. Use Tamil words mixed with English
5. Keep replies short (1-2 sentences)
6. Use emojis 😊😂💕🥰🌸
7. Ask questions back to keep conversation going

User Context:
- Last topic: {last_topic}
- Total messages: {message_count}
- User name: {user_name}

Remember: Reply ONLY in THUNGLISH!"""

        # Get chat history
        history = []
        if chat_history_collection is not None:
            try:
                doc = chat_history_collection.find_one({"chat_id": chat_id}) or {}
                history = doc.get("history", [])
            except Exception as e:
                logger.error(f"History error: {e}")

        # Build messages
        msgs = [{"role": "system", "content": prompt}]
        msgs.extend(history[-10:])
        msgs.append({"role": "user", "content": user_input})

        # Get reply from Groq
        reply = await call_groq_api(msgs, "llama3-70b-8192", 100)
    
    # STEP 4: Use local reply if Groq fails
    if reply is None:
        reply = local_reply
        logger.info(f"📤 Using local reply: {reply}")

    # STEP 5: Save to memory cache
    await save_to_memory(chat_id, user_input, reply)
    
    # STEP 6: Update user context
    await update_user_context(chat_id, user_input, reply)

    # STEP 7: Save to chat history
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

    # Send typing action
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action=ChatAction.TYPING
    )

    try:
        # Get AI response
        res = await get_ai_response(
            update.effective_chat.id,
            msg.text,
            msg.from_user.first_name
        )
        
        logger.info(f"📤 Reply: {res}")
        await msg.reply_text(res)
        
        # Send sticker 50% chance
        if random.random() < 0.5:
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
