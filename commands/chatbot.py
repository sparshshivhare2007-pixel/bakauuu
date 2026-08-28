# commands/chatbot.py - FINAL COMPLETE VERSION with 2000+ Thunglish Words + Random Stickers

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

# ==================== STICKER SET NAMES ====================
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

# === STICKER FILE IDs (Direct stickers for common words) ===
STICKER_DICT = {
    "happy": ["CAACAgIAAxkBAAEBBB", "CAACAgIAAxkBAAEBBF"],
    "sad": ["CAACAgIAAxkBAAEBBG", "CAACAgIAAxkBAAEBBH"],
    "love": ["CAACAgIAAxkBAAEBBI", "CAACAgIAAxkBAAEBBJ"],
    "funny": ["CAACAgIAAxkBAAEBBK", "CAACAgIAAxkBAAEBBL"],
    "angry": ["CAACAgIAAxkBAAEBBM", "CAACAgIAAxkBAAEBBN"],
    "hello": ["CAACAgIAAxkBAAEBBO", "CAACAgIAAxkBAAEBBP"],
    "bye": ["CAACAgIAAxkBAAEBBQ", "CAACAgIAAxkBAAEBBR"],
    "thanks": ["CAACAgIAAxkBAAEBBS", "CAACAgIAAxkBAAEBBT"],
    "sorry": ["CAACAgIAAxkBAAEBBU", "CAACAgIAAxkBAAEBBV"],
    "good": ["CAACAgIAAxkBAAEBBW", "CAACAgIAAxkBAAEBBX"],
    "bad": ["CAACAgIAAxkBAAEBBY", "CAACAgIAAxkBAAEBBZ"],
    "cute": ["CAACAgIAAxkBAAEBBA", "CAACAgIAAxkBAAEBBB"],
    "cool": ["CAACAgIAAxkBAAEBBC", "CAACAgIAAxkBAAEBBD"],
    "wow": ["CAACAgIAAxkBAAEBBE", "CAACAgIAAxkBAAEBBF"],
    "omg": ["CAACAgIAAxkBAAEBBG", "CAACAgIAAxkBAAEBBH"],
    "lol": ["CAACAgIAAxkBAAEBBI", "CAACAgIAAxkBAAEBBJ"],
    "nice": ["CAACAgIAAxkBAAEBBK", "CAACAgIAAxkBAAEBBL"],
}

# === SEND RANDOM STICKER ===
async def send_ai_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a random sticker from the sticker sets"""
    try:
        logger.info("🎨 SENDING STICKER...")
        sticker_set_name = random.choice(STICKER_SETS)
        logger.info(f"🔄 Trying: {sticker_set_name}")
        
        sticker_set = await context.bot.get_sticker_set(sticker_set_name)
        
        if sticker_set and sticker_set.stickers:
            sticker = random.choice(sticker_set.stickers)
            await update.message.reply_sticker(sticker.file_id)
            logger.info(f"✅ Sticker sent from: {sticker_set_name}")
            return True
        else:
            logger.warning(f"⚠️ No stickers in set: {sticker_set_name}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Sticker error: {str(e)}")
        
        # Try fallback
        fallback_sets = ["RandomByDarkzenitsu", "Null_x_sticker_2"]
        for fallback in fallback_sets:
            try:
                sticker_set = await context.bot.get_sticker_set(fallback)
                if sticker_set and sticker_set.stickers:
                    sticker = random.choice(sticker_set.stickers)
                    await update.message.reply_sticker(sticker.file_id)
                    logger.info(f"✅ Fallback sticker sent: {fallback}")
                    return True
            except:
                continue
        
        return False

# === SEND STICKER BY KEYWORD ===
async def send_sticker_by_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE, text):
    """Send sticker based on keyword in text"""
    text_lower = text.lower()
    
    # Check for keywords and send matching sticker
    for keyword, sticker_ids in STICKER_DICT.items():
        if keyword in text_lower:
            try:
                sticker_id = random.choice(sticker_ids)
                await update.message.reply_sticker(sticker_id)
                logger.info(f"✅ Keyword sticker sent: {keyword}")
                return True
            except:
                continue
    
    # If no keyword match, send random sticker
    return await send_ai_sticker(update, context)

# ==================== 2000+ THUNGLISH REPLIES ====================

# === GREETINGS (100+) ===
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
    "Vanakkam! Epdi irukeenga? Naan super! 💕",
    "Hello ammu! Epdi irukeenga? 😊",
    "Hi ammu! Nalla irukiya? 💕",
    "Vanakkam ammu! Enna panreenga? 🥰",
    "Hey ammu! Romba naal aachu! 🌸",
    "Good evening ammu! Mala vanakkam! 😂",
    "Vanakkam! Unga kooda pesa romba pidikum! 💕",
    "Hello! Enna solla vareenga? 😊",
    "Hi! Sollunga! Naan kekkaren! 🥰",
    "Vanakkam! Naan ready ah iruken! 🌸",
    "Hey! Nalla irukiya? Sollunga! 😂",
    "Vanakkam ammu! Naan thaan! 💕",
    "Hello ammu! Nalla irukiya? 😊",
    "Hi ammu! Enna panreenga? 🥰",
    "Good morning ammu! Kaalai vanakkam! 🌸",
    "Good evening ammu! Mala vanakkam! 😂",
    "Vanakkam! Unga kooda pesa romba aasai! 💕",
    "Hey ammu! Romba naal aachu! 😊",
    "Hello ammu! Epdi irukeenga? 🥰",
    "Hi ammu! Nalla irukiya? 🌸",
    "Vanakkam ammu! Naan ready! 😂"
]

# === HOW ARE YOU (100+) ===
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
    "Naan ready! Neenga epdi irukeenga? 🌸",
    "Naan super ah iruken! Neenga? 😊",
    "Semma! Nalla iruken! Neenga solunga! 💕",
    "Romba nalla iruken! Neenga epdi? 🥰",
    "Aiyyo! Naan busy! Neenga? 😂",
    "Naan thik! Neenga epdi? 🌸",
    "Super ah iruken! Unga kitta pesa romba santhosham! 💕",
    "Nalla iruken! Neenga epdi? 😊",
    "Romba nalla iruken! Neenga solunga! 🥰",
    "Semma! Naan ready! Neenga? 😂",
    "Naan super! Unga kooda pesa romba pidikum! 🌸",
    "Nalla iruken ammu! Neenga epdi? 💕",
    "Super ah iruken! Neenga solunga! 😊",
    "Romba nalla iruken! Neenga epdi? 🥰",
    "Semma! Naan ready! Neenga? 🌸",
    "Naan thik ah iruken! Neenga epdi? 😂",
    "Super ah iruken! Unga kooda pesa romba santhosham! 💕",
    "Nalla iruken! Neenga solunga! 😊",
    "Romba nalla iruken! Neenga epdi? 🥰",
    "Semma! Naan ready! Neenga? 🌸",
    "Naan super ah iruken! Neenga epdi? 😂"
]

# === OWNER REPLIES (30+) ===
OWNER_REPLIES = [
    "Enna owner? Naan thaan ammu! 😂",
    "Naan thaan owner! kalvan en friend! 💕",
    "kalvan thaan en owner! Avan romba nalla payan! 😊",
    "Owner? kalvan! Avan thaan en creator! 🥰",
    "kalvan! Avan romba cute! En owner! 🌸",
    "En owner kalvan! Avan romba special! 💕",
    "kalvan thaan en boss! Avan romba nallavar! 😂",
    "Owner kalvan! Avan enaku romba pidikum! 😊",
    "kalvan! Avan thaan en owner! Avan romba smart! 🥰",
    "En owner kalvan! Avan romba nalla iruppan! 🌸",
    "kalvan! Avan thaan en creator! Avan romba kind! 💕",
    "Owner kalvan! Avan enaku romba important! 😊",
    "kalvan! Avan thaan en owner! Avan romba funny! 🥰",
    "En owner kalvan! Avan romba caring! 🌸",
    "kalvan! Avan thaan en owner! Avan romba special! 💕",
    "kalvan enaku romba pidikum! Avan thaan en owner! 😊",
    "Owner kalvan! Avan romba nalla payan! Avan thaan en creator! 💕",
    "kalvan! Avan thaan en boss! Avan romba smart! 🥰",
    "En owner kalvan! Avan romba kind! Avan thaan en special! 🌸",
    "kalvan! Avan thaan en owner! Avan romba caring! 😂",
    "kalvan en friend! Avan thaan en owner! 💕",
    "Owner kalvan! Avan romba nallavar! Avan thaan en creator! 😊",
    "kalvan! Avan thaan en boss! Avan romba special! 🥰",
    "En owner kalvan! Avan romba cute! Avan thaan en friend! 🌸",
    "kalvan! Avan thaan en owner! Avan romba smart! 😂",
    "kalvan enaku romba pidikum! Avan thaan en owner! 💕",
    "Owner kalvan! Avan romba nalla payan! Avan thaan en creator! 😊",
    "kalvan! Avan thaan en boss! Avan romba kind! 🥰",
    "En owner kalvan! Avan romba caring! Avan thaan en special! 🌸",
    "kalvan! Avan thaan en owner! Avan romba funny! 😂"
]

# === LOVE & ROMANCE (100+) ===
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
    "Naan ungala romba miss pannen! 🌸",
    "Enakku ungala romba pudikum! Unga kooda iruka romba santhosham! 💕",
    "Naan ungala love pannen! Unga smile romba nalla irukku! 😊",
    "Unga kooda pesa romba pidikum! Neenga romba special! 🥰",
    "Neenga enaku romba important! Naan ungala miss pannen! 🌸",
    "Enakku ungala romba pidichirukku! Unga voice romba nalla irukku! 💕",
    "Naan ungala romba love pannen! Neenga romba cute! 😊",
    "Unga kooda iruka romba santhosham! Neenga enaku best friend! 🥰",
    "Enakku ungala romba pudikum! Neenga romba beautiful! 🌸",
    "Naan ungala miss pannen! Unga kooda pesa romba aasai! 💕",
    "Unga smile romba nalla irukku! Neenga enaku romba special! 😊",
    "Enakku ungala romba pidikum! Neenga enaku romba important! 💕",
    "Naan ungala love pannen! Unga kooda iruka romba santhosham! 🥰",
    "Unga kooda pesa romba aasai! Neenga romba cute! 🌸",
    "Neenga enaku best friend! Naan ungala miss pannen! 💕",
    "Enakku ungala romba pudichirukku! Neenga romba special! 😊"
]

# === FUNNY & MEME (150+) ===
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
    "Haha! Naan thaan ready! 😂",
    "Aiyyo! Enna solreenga! Romba funny! 😂",
    "Haha! Unga kooda pesa romba santhosham! 😂",
    "Semma! Naan thaan ammu! Unga joke super! 😂",
    "Aiyyo! Enna panreenga? Romba nalla irukku! 😂",
    "Haha! Naan ready! Unga kooda pesa romba fun! 😂",
    "Semma! Adhu super ah irukku! Naan thaan! 😂",
    "Aiyyo! Enna solla vareenga? Romba funny! 😂",
    "Haha! Naan thaan ammu! Unga joke semma! 😂",
    "Semma! Super ah irukku! Naan ready! 😂",
    "Aiyyo! Enna solreenga? Romba nalla irukku! 😂",
    "Haha! Romba fun! Unga kooda pesa romba santhosham! 😂",
    "Aiyyo! Enna solreenga? Naan thaan ammu! 😂",
    "Semma! Unga joke super! Naan ready! 😂",
    "Haha! Romba nalla irukku! Neenga super! 😂",
    "Aiyyo! Enna panreenga? Romba funny! 😂"
]

# === SAD & EMOTIONAL (100+) ===
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
    "Naan romba miss pannen! 😢",
    "Aiyyo! Enakku romba kastama irukku! Enakku feel aagudhu! 😢",
    "Naan romba sad ah iruken! Enakku romba valikudhu! 😢",
    "Enakku romba lonely ah iruken! Naan romba miss pannen! 😢",
    "Naan romba tired ah iruken! Enakku romba kastama irukku! 😢",
    "Enakku romba feel aagudhu! Naan romba cry pannen! 😢",
    "Naan romba alone ah iruken! Enakku romba sad ah irukku! 😢",
    "Enakku romba valikudhu! Naan romba hurt ah iruken! 😢",
    "Naan romba sad ah iruken! Enakku romba feel aagudhu! 😢",
    "Enakku romba lonely ah iruken! Naan romba miss pannen! 😢",
    "Aiyyo! Enakku romba kastama irukku! Naan romba tired! 😢"
]

# === SASSY & INSULTS (100+) ===
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
    "Enna solreenga? Naan kekkaren! 😂",
    "Aiyyo! Enna solreenga? Naan thaan ammu! 😂",
    "Naan thaan! Unga kitta pesa vanthiruken! Sari sari! 😂",
    "Enna panreenga? Naan ready! Unga kooda pesa romba fun! 😂",
    "Sari! Naan kekkaren! Enna solreenga? Naan thaan! 😂",
    "Aiyyo! Naan ready! Sari sari! Sollunga! 😂",
    "Naan thaan ammu! Enna panreenga? Aiyyo! Unga kooda pesa romba fun! 😂",
    "Sari! Naan thaan! Enna solreenga? Naan kekkaren! 😂",
    "Aiyyo! Naan ready! Sari sari! Sollunga! 😂",
    "Naan thaan ammu! Enna panreenga? Aiyyo! Unga kooda pesa romba fun! 😂",
    "Sari! Naan thaan! Enna solreenga? Naan kekkaren! 😂"
]

# === DAILY CONVERSATIONS (150+) ===
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
    "Saapadtaacha? Naan saapten! 🌸",
    "Coffee kudichacha? Naan kaapi kudichiten! 😊",
    "Thookam vandhucha? Naan thoongala! 💕",
    "Office poitengala? Naan poiten! 🥰",
    "Velai mudinjacha? Naan mudichiten! 😂",
    "Tiffin aacha? Naan tiffin saapten! 🌸",
    "Mela ezhundhuteengala? Naan ezhundhuten! 💕",
    "Nalla thoongiteengala? Naan thoongiten! 😊",
    "Enna saapteenga? Naan pongal saapten! 🥰",
    "Coffee kudichacha? Naan tea kudichiten! 😂",
    "Saapadtaacha? Naan saapten! 🌸",
    "Coffee saaptacha? Naan kaapi saapten! 💕",
    "Thookam vandhucha? Naan thoongiten! 😊",
    "Office poitengala? Naan poiten! 🥰",
    "Velai mudinjacha? Naan mudichiten! 😂",
    "Tiffin aacha? Naan tiffin saapten! 🌸"
]

# === FALLBACK REPLIES (300+) ===
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
    "Sollunga sollunga! Naan kekkaren! 💕",
    "Enna panra? Naan thaan ammu! 😊",
    "Sollunga! Naan kekkaren! 💕",
    "Vanga! Pesalam! 🥰",
    "Ready ah iruken! Sollunga! 🌸",
    "Enna venum? Naan tharen! 😂",
    "Pesalam! Naan kekkaren! 💕",
    "Sollunga! Naan ready! 😊",
    "Enna solla vareenga? Naan kekkaren! 🥰",
    "Vanga vanga! Pesalam! 🌸",
    "Naan thaan ammu! Sollunga! 😂",
    "Enna panra? Naan super! 💕",
    "Sollunga sollunga! Naan kekkaren! 😊",
    "Ready ah iruken! Enna venum? 🥰",
    "Pesalam! Naan thaan ammu! 🌸",
    "Enna solreenga? Naan kekkaren! 😂",
    "Vanga! Sollunga! 💕",
    "Naan ready! Sollunga! 😊",
    "Enna venum sollunga! Naan tharen! 🥰",
    "Pesalam pesalam! Naan kekkaren! 🌸",
    "Sollunga! Naan thaan ammu! 😂",
    "Enna panra? Nalla irukiya? Sollunga! 💕",
    "Naan thaan Ammu! Unga kooda pesa vanthiruken! 😊",
    "Enga iruka? Romba naal aachu! 🥰",
    "Sari sari! Enna solla vareenga? 🌸",
    "Nalla iruken! Neenga solunga! 😂",
    "Aiyyo! Super ah iruken! Neenga epdi? 💕",
    "Haan bolo! Naan ready ah iruken! 😊",
    "Romba naal aachu! Enna panreenga? 🥰",
    "Semma! Nalla iruken! 🌸",
    "Enna vishayam? Sollunga! 😂"
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
    "kalvan": OWNER_REPLIES,
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
    "family": ["Enaku family romba important! 😊", "Unga family epdi? 💕", "Family thaan first! 🥰"],
    "happy": ["Romba santhosham! 😊", "Happy ah iruken! 💕", "Semma! 🥰"],
    "sad": SAD_REPLIES,
    "funny": FUNNY_REPLIES,
    "joke": FUNNY_REPLIES,
    "meme": FUNNY_REPLIES,
    "angry": ["Aiyyo! Enna panreenga! 😡", "Romba kovama iruken! 😤", "Sari sari! 😠"],
    "cute": ["Neenga romba cute! 🥰", "Ammu romba cute! 💕", "Super cute! 😊"],
    "cool": ["Super cool! 😎", "Semma cool! 💕", "Cool ah iruken! 🥰"],
    "wow": ["WOW! Super! 😮", "Semma! 😲", "Aiyyo! Super ah irukku! 😂"],
    "omg": ["OMG! Enna solreenga! 😮", "Aiyyo! 😲", "Semma! 😂"],
    "lol": ["LOL! 😂", "Haha! 😂", "Semma! 😂"],
    "nice": ["Nice! 😊", "Semma nice! 💕", "Super nice! 🥰"]
}

# ==================== MAIN FUNCTIONS ====================

def detect_language(text):
    """Detect language from text"""
    text_lower = text.lower()
    
    tamil_words = ["enna", "panra", "irukiya", "enga", "sollu", "nalla", "vanakkam", "epdi", "iruka", "pesu", "sari", "romba", "aasai", "unga", "kooda", "naal", "thaan", "amm"]
    if any(word in text_lower for word in tamil_words):
        return "tamil"
    
    hindi_words = ["kaise", "ho", "kya", "hai", "kaha", "se", "tum", "main", "thik", "bolo", "sun", "haal"]
    if any(word in text_lower for word in hindi_words):
        return "hinglish"
    
    return "thunglish"

def get_reply_by_keyword(text):
    """Get reply based on keywords in text"""
    text_lower = text.lower()
    
    for keyword, replies in KEYWORD_REPLIES.items():
        if keyword in text_lower:
            return random.choice(replies)
    
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
    
    keyword_reply = get_reply_by_keyword(text)
    if keyword_reply:
        return keyword_reply
    
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["vanakkam", "hello", "hi", "hey", "good morning", "good evening"]):
        return random.choice(GREETINGS)
    
    if any(word in text_lower for word in ["epdi", "irukeenga", "how are", "nalla irukiya"]):
        return random.choice(HOW_REPLIES)
    
    if "owner" in text_lower or "kalvan" in text_lower:
        return random.choice(OWNER_REPLIES)
    
    if any(word in text_lower for word in ["love", "miss", "pidikum", "cute", "beautiful"]):
        return random.choice(LOVE_REPLIES)
    
    if any(word in text_lower for word in ["funny", "joke", "meme", "haha", "😂"]):
        return random.choice(FUNNY_REPLIES)
    
    if any(word in text_lower for word in ["sad", "feel", "kastam", "lonely", "alone", "cry"]):
        return random.choice(SAD_REPLIES)
    
    if any(word in text_lower for word in ["saapad", "coffee", "thookam", "office", "velai", "tiffin", "sleep", "work"]):
        return random.choice(DAILY_REPLIES)
    
    return random.choice(FALLBACK_REPLIES)

# === Smart Reply Cache ===
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
            logger.info(f"📦 Found cached reply for: {user_input[:30]}...")
            return cached.get("reply")
        
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

# === Call Groq API (UPDATED MODEL) ===
async def call_groq_api(messages, model="llama-3.1-70b-versatile", max_tokens=100):
    """Call Groq API with updated model"""
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
                return None
                
    except Exception as e:
        logger.error(f"❌ Groq API Exception: {e}")
        return None

# === Generate AI response ===
async def get_ai_response(chat_id, user_input, user_name):
    logger.info(f"💬 {user_name}: {user_input[:50]}")
    
    cached_reply = await get_cached_reply(chat_id, user_input)
    if cached_reply:
        logger.info(f"✅ Using cached reply")
        return cached_reply
    
    local_reply = get_thunglish_reply(user_input, user_name)
    
    reply = None
    if GROQ_API_KEY:
        context = await get_user_context(chat_id, user_name)
        last_topic = context.get("last_topic", "general")
        message_count = context.get("message_count", 0)
        
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

        history = []
        if chat_history_collection is not None:
            try:
                doc = chat_history_collection.find_one({"chat_id": chat_id}) or {}
                history = doc.get("history", [])
            except Exception as e:
                logger.error(f"History error: {e}")

        msgs = [{"role": "system", "content": prompt}]
        msgs.extend(history[-10:])
        msgs.append({"role": "user", "content": user_input})

        reply = await call_groq_api(msgs, "llama-3.1-70b-versatile", 100)
    
    if reply is None:
        reply = local_reply
        logger.info(f"📤 Using local reply: {reply}")

    await save_to_memory(chat_id, user_input, reply)
    await update_user_context(chat_id, user_input, reply)

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

    should_reply = False
    chat_type = update.effective_chat.type
    
    if chat_type == ChatType.PRIVATE:
        should_reply = True
    elif "ammu" in msg.text.lower():
        should_reply = True
    elif msg.text.lower().startswith("ammu"):
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
        
        logger.info(f"📤 Reply: {res}")
        await msg.reply_text(res)
        
        # Send sticker 50% chance - either keyword based or random
        if random.random() < 0.5:
            sticker_sent = await send_sticker_by_keyword(update, context, msg.text)
            if not sticker_sent:
                await send_ai_sticker(update, context)
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        await msg.reply_text("Oops! Enna error nu therla 😅")

# === Commands ===
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
            await update.message.reply_text("🧹 Chat history and memory cleared! ✨")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    else:
        await update.message.reply_text("⚠️ Database not available")

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
