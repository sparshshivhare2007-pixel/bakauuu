# chatbot.py
# Final BAKA Chatbot - Stickers, Emoji, Short Replies, Models

import os, random, httpx
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction, ChatType, ParseMode
from dotenv import load_dotenv

# Load API keys from .env
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
CODESTRAL_API_KEY = os.getenv("CODESTRAL_API_KEY")

# MongoDB chat history
try:
    from pymongo import MongoClient
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(MONGO_URI)
    chatbot_collection = client.baka.chat_history
except:
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
    "https://t.me/addstickers/RandomByDarkzenitsu", "https://t.me/addstickers/Null_x_sticker_2",
    "https://t.me/addstickers/pack_73bc9_by_TgEmojis_bot", "https://t.me/addstickers/animation_0_8_Cat",
    "https://t.me/addstickers/vhelw_by_CalsiBot", "https://t.me/addstickers/Rohan_yad4v1745993687601_by_toWebmBot",
    "https://t.me/addstickers/MySet199", "https://t.me/addstickers/Quby741", "https://t.me/addstickers/Animalsasthegtjtky_by_fStikBot",
    "https://t.me/addstickers/a6962237343_by_Marin_Roxbot", "https://t.me/addstickers/cybercats_stickers"
]

# === Send random sticker ===
async def send_ai_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pack = random.choice(STICKER_PACKS)
        s = await context.bot.get_sticker_set(pack)
        if s.stickers:
            await update.message.reply_sticker(random.choice(s.stickers).file_id)
    except: 
        pass

# === Call AI model API ===
async def call_model_api(provider, messages, max_tokens=50):
    conf = MODELS.get(provider)
    if not conf or not conf["key"]: 
        return None
    async with httpx.AsyncClient(timeout=25) as client:
        try:
            resp = await client.post(
                conf["url"],
                json={"model": conf["model"], "messages": messages, "max_tokens": max_tokens},
                headers={"Authorization": f"Bearer {conf['key']}"}
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            else:
                print(f"API Error: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"API Exception: {e}")
            return None
    return None

# === Generate AI response ===
async def get_ai_response(chat_id, user_input, user_name, model="mistral"):
    is_code = any(k in user_input.lower() for k in ["code", "python", "fix", "debug"])
    active_model = "codestral" if is_code else model
    tokens = 4096 if is_code else 50

    prompt = f"You are BAKA AI, a cute sassy Hinglish girl. Reply in 1 short sentence only. User: {user_name}"

    history = []
    if chatbot_collection is not None:
        doc = chatbot_collection.find_one({"chat_id": chat_id}) or {}
        history = doc.get("history", [])

    msgs = [{"role": "system", "content": prompt}] + history[-6:] + [{"role": "user", "content": user_input}]

    reply = await call_model_api(active_model, msgs, tokens)
    
    if reply is None:
        reply = "Main thik hu, tum kaise ho? 😊"

    # Save history
    if chatbot_collection is not None:
        chatbot_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"history": (history + [{"role":"user","content":user_input},{"role":"assistant","content":reply}])[-10:]}},
            upsert=True
        )
    return reply, is_code

# === Automatic AI message handler ===
async def ai_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text or msg.text.startswith("/"):
        return

    # Check if bot should reply - ONLY "ammu"
    should_reply = (
        update.effective_chat.type == ChatType.PRIVATE
        or (msg.reply_to_message and msg.reply_to_message.from_user.id == context.bot.id)
        or msg.text.lower().startswith("ammu")  # Sirf "ammu" se start
        or "ammu" in msg.text.lower()  # Ya kahin bhi "ammu" ho
    )
    
    if should_reply:
        print(f"Replying to: {msg.text}")  # Debug log
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        res, code = await get_ai_response(update.effective_chat.id, msg.text, msg.from_user.first_name)

        # Send response
        await msg.reply_text(res if code else nezuko_style(res))
        
        # Send a random sticker 80% of the time
        if random.random() < 0.8:
            await send_ai_sticker(update, context)

# === /ask command handler ===
async def ask_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💬 Please type something after /ask")
        return
    user_input = " ".join(context.args)
    res, code = await get_ai_response(update.effective_chat.id, user_input, update.effective_user.first_name)
    await update.message.reply_text(res if code else nezuko_style(res))
