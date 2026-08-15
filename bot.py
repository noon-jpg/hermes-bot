import json
import os
from telegram.ext import Updater, CommandHandler
 

import os
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

# ======== CONFIG ========
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "nousresearch/hermes-3-llama-3.1-70b"

PORT = int(os.environ.get("PORT", 8443))
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "https://hermes-bot-1ox1.onrender.com")
# =========================

app = Flask(__name__)


telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

async def handle_message(update: Update, context):
    user_text = update.message.text
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
   
    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": user_text}],
        "max_tokens": 1000 
    }
   
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=data, timeout=30)
       
        
        if response.status_code != 200:
            ai_reply = f"Error: OpenRouter returned status {response.status_code}: {response.text[:200]}"
        else:
            try:
                res_json = response.json()
                if "choices" in res_json and len(res_json["choices"]) > 0:
                    ai_reply = res_json["choices"][0]["message"]["content"]
                else:
                    ai_reply = f"Error: Unexpected response structure: {res_json}"
            except json.JSONDecodeError:
                ai_reply = f"Error: Failed to parse JSON from OpenRouter. Response text: {response.text[:200]}"
                
    except Exception as e:
        ai_reply = f"Sorry, I ran into an error: {e}"
        
    await update.message.reply_text(ai_reply)

telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    if request.method == "POST":
        import asyncio
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        
        async def process():
            await telegram_app.initialize()
            await telegram_app.process_update(update)
            
        asyncio.run(process())
        return "OK", 200

@app.route("/")
def index():
    return "Bot is running on Render!"

if __name__ == "__main__":
    if RENDER_URL:
        webhook_url = f"{RENDER_URL}/{TELEGRAM_TOKEN}"
       
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={webhook_url}")
        print("Webhook set to:", webhook_url)
    
    app.run(host="0.0.0.0", port=PORT)
