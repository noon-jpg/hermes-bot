import os
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# ======== CONFIG ========

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "nousresearch/hermes-3-llama-3.1-70b"


RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "")
PORT = int(os.environ.get("PORT", 8443))
# =========================

app = Flask(__name__)


telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

async def start(update: Update, context):
    await update.message.reply_text("Hi! I'm Hermes 3 on Telegram. Ask me anything.")

async def handle_message(update: Update, context):
    user_text = update.message.text

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": user_text}]
    }

try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=data)
        print("OpenRouter Status:", response.status_code)
        print("OpenRouter Response:", response.text)
        response.raise_for_status()
        res_json = response.json()
        
        if "choices" in res_json and len(res_json["choices"]) > 0:
            ai_reply = res_json["choices"][0]["message"]["content"]
        else:
            ai_reply = f"Error: Unexpected response structure: {res_json}"
            
    except Exception as e:
        ai_reply = f"Sorry, I ran into an error: {e}"  
  
except Exception as e:
  ai_reply = f"Sorry, I ran into an error: {e}"

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
   
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)

    import asyncio
    asyncio.run(telegram_app.initialize())
    asyncio.run(telegram_app.process_update(update))
    return "OK", 200

@app.route("/")
def index():
    return "Bot is running on Render!"

if __name__ == "__main__":

    RENDER_URL = "https://hermes-bot-1ox1.onrender.com" 
    webhook_url = f"{RENDER_URL}/{TELEGRAM_TOKEN}"
    
    # إرسال طلب تفعيل الـ Webhook إلى تيليجرام
    response = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={webhook_url}")
    print("Set Webhook Response:", response.text)
    
    # تشغيل السيرفر
    app.run(host="0.0.0.0", port=PORT)
