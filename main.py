import telebot
from telebot import types
import threading
import time
import os
import requests
from pyrogram import Client
from gradio_client import Client as GradioClient
import database  # Tumhari database.py file
import keep_alive # Server ko zinda rakhne ke liye

# --- ⚙️ CONFIGURATION (Yahan Apni Details Dubara Daalo) ---
BOT_TOKEN = "8587568228:AAG5zI9Bvlm3p6aSQlgzIFfOHcnUybxAFwY"      # BotFather wala Token
API_ID = 20695130                        # Telegram API ID
API_HASH = "530ea887626566c365a046c01635ee67"        # Telegram API Hash
PASSWORD = "Boss1"                      # Bot ka Password

# Voice Changer AI Link (Ye demo link hai)
HF_SPACE_URL = "juuxn/RVC-Demo" 

bot = telebot.TeleBot(BOT_TOKEN)

# ==========================================
# 🔐 1. SECURITY SYSTEM (LOGIN)
# ==========================================

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    
    # Check Database
    if database.is_user_allowed(user_id):
        show_main_menu(message)
    else:
        msg = bot.send_message(message.chat.id, "⛔ **System Locked!**\nPlease enter the Password:")
        bot.register_next_step_handler(msg, check_password)

def check_password(message):
    if message.text == PASSWORD:
        database.add_allowed_user(message.from_user.id)
        bot.reply_to(message, "✅ **Access Granted!** Welcome Boss.")
        show_main_menu(message)
    else:
        bot.reply_to(message, "❌ **Wrong Password!** Try again /start")

def show_main_menu(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("➕ Add Bot Token")
    btn2 = types.KeyboardButton("👤 Add Account")
    btn3 = types.KeyboardButton("📊 Check Stats")
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, "👋 **Main Menu:** Select an Option", reply_markup=markup)

# ==========================================
# ⚙️ 2. ADMIN PANEL (ADD BOTS/ACCOUNTS)
# ==========================================

@bot.message_handler(func=lambda m: m.text == "➕ Add Bot Token")
def add_token_step(message):
    msg = bot.reply_to(message, "🤖 **Send Bot Token** (from BotFather):")
    bot.register_next_step_handler(msg, save_token)

def save_token(message):
    token = message.text.strip()
    if database.add_bot_token(token):
        bot.reply_to(message, f"✅ **Bot Added!**\nToken saved to Database.")
    else:
        bot.reply_to(message, "⚠️ Token already exists!")

@bot.message_handler(func=lambda m: m.text == "👤 Add Account")
def add_session_step(message):
    msg = bot.reply_to(message, "👤 **Send Pyrogram String Session**:\n(For Auto Views + Reactions)")
    bot.register_next_step_handler(msg, save_session)

def save_session(message):
    session = message.text.strip()
    if database.add_user_session(session):
        bot.reply_to(message, f"✅ **Account Added!**\nSession saved to Database.")
    else:
        bot.reply_to(message, "⚠️ Session already exists!")

@bot.message_handler(func=lambda m: m.text == "📊 Check Stats")
def stats(message):
    tokens = len(database.get_all_tokens())
    sessions = len(database.get_all_sessions())
    bot.reply_to(message, f"📊 **System Power:**\n\n🤖 Worker Bots: `{tokens}`\n👤 User Accounts: `{sessions}`")

# ==========================================
# 🎤 3. VOICE CHANGER (AI SYSTEM)
# ==========================================

@bot.message_handler(content_types=['voice', 'audio'])
def handle_audio(message):
    # Voice Selection Buttons
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👨 Male Voice", callback_data="voice_male"))
    markup.add(types.InlineKeyboardButton("👩 Female Voice", callback_data="voice_female"))
    markup.add(types.InlineKeyboardButton("👦 Teenage Boy", callback_data="voice_boy"))
    
    bot.reply_to(message, "🎤 **Select Voice Effect:**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("voice_"))
def process_voice(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "🔄 **Downloading Audio...**")
    
    try:
        # 1. Download File
        if call.message.reply_to_message.voice:
            file_id = call.message.reply_to_message.voice.file_id
        else:
            file_id = call.message.reply_to_message.audio.file_id
            
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        filename = f"user_{call.message.chat.id}.ogg"
        with open(filename, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        # 2. Loading Animation
        bot.edit_message_text("🔄 **Converting Voice (AI)...** 🌑", chat_id=msg.chat.id, message_id=msg.message_id)
        
        # Select Model
        model_index = 0 
        if call.data == "voice_female": model_index = 1
        elif call.data == "voice_boy": model_index = 2 
        
        # 3. Call AI
        client_hf = GradioClient(HF_SPACE_URL)
        result = client_hf.predict(
            filename, model_index, 0, "pm", api_name="/predict"
        )
        
        # 4. Send Result
        with open(result, 'rb') as audio:
            bot.send_voice(call.message.chat.id, audio, caption="✨ Voice Changed Successfully!")
        
        # Cleanup
        bot.delete_message(msg.chat.id, msg.message_id)
        os.remove(filename)
        
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", chat_id=msg.chat.id, message_id=msg.message_id)

# ==========================================
# 🔥 4. AUTO REACTION & VIEWS ENGINE
# ==========================================

@bot.channel_post_handler(content_types=['text', 'photo', 'video', 'document'])
def auto_react_monitor(message):
    if message.chat.username:
        print(f"🔥 New Post: {message.chat.username}/{message.message_id}")
        threading.Thread(target=perform_mass_action, args=(message.chat.username, message.message_id)).start()

def perform_mass_action(username, message_id):
    emoji = "🔥"
    
    # User Accounts (Views + React)
    sessions = database.get_all_sessions()
    for session in sessions:
        try:
            app = Client("temp", api_id=API_ID, api_hash=API_HASH, session_string=session, in_memory=True, no_updates=True)
            app.start()
            app.get_messages(username, message_id)
            app.send_reaction(username, message_id, emoji)
            app.stop()
            time.sleep(1)
        except:
            pass

    # Worker Bots (Only React)
    tokens = database.get_all_tokens()
    for token in tokens:
        try:
            url = f"https://api.telegram.org/bot{token}/setMessageReaction"
            payload = {
                "chat_id": f"@{username}",
                "message_id": message_id,
                "reaction": [{"type": "emoji", "emoji": emoji}]
            }
            requests.post(url, json=payload, timeout=5)
        except:
            pass

# --- START ---
keep_alive.keep_alive()
print("🚀 Bot is Live...")
bot.polling(non_stop=True)
