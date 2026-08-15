import os
import logging
import json
import asyncio
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

# ======== CONFIG & LOGGING ========
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

if not TELEGRAM_TOKEN or not OPENROUTER_API_KEY:
    logger.error("CRITICAL: TELEGRAM_TOKEN and OPENROUTER_API_KEY must be set in environment variables!")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "nousresearch/hermes-3-llama-3.1-70b"

PORT = int(os.environ.get("PORT", 8443))
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

app = Flask(__name__)

# Initialize PTB application
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

async def handle_message(update: Update, context):
    user_text = update.message.text
    logger.info(f"Received message from user: {user_text}")
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": RENDER_URL or "https://render.com", 
        "X-Title": "Hermes Bot"
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
            logger.error(ai_reply)
        else:
            try:
                res_json = response.json()
                if "choices" in res_json and len(res_json["choices"]) > 0:
                    ai_reply = res_json["choices"][0]["message"]["content"]
                else:
                    ai_reply = f"Error: Unexpected response structure: {res_json}"
                    logger.error(ai_reply)
            except json.JSONDecodeError:
                ai_reply = f"Error: Failed to parse JSON from OpenRouter."
                logger.error(f"{ai_reply} Response: {response.text[:200]}")
                
    except Exception as e:
        ai_reply = f"Sorry, I ran into an error processing your request."
        logger.exception(f"Exception during OpenRouter call: {e}")
        
    await update.message.reply_text(ai_reply)

# Register message handler
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    """Endpoint that Telegram calls when a new message arrives."""
    if request.method == "POST":
        try:
            json_data = request.get_json(force=True)
            logger.info("Incoming webhook update received.")
            update = Update.de_json(json_data, telegram_app.bot)
            
            async def process():
                await telegram_app.initialize()
                await telegram_app.process_update(update)
                
            # تشغيل الحدث بشكل صحيح داخل Flask
            asyncio.run(process())
        except Exception as e:
            logger.exception(f"Error processing webhook update: {e}")
            return "Internal Server Error", 500
            
        return "OK", 200

@app.route("/")
def index():
    return "Bot is running on Render!"

if __name__ == "__main__":
    if RENDER_URL:
        webhook_url = f"{RENDER_URL}/{TELEGRAM_TOKEN}"
        logger.info(f"Setting webhook to: {webhook_url}")
        
        try:
            r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={webhook_url}")
            logger.info(f"Telegram setWebhook response: {r.text}")
        except Exception as e:
            logger.error(f"Failed to set webhook automatically: {e}")
    else:
        logger.warning("RENDER_EXTERNAL_URL not found. Webhook auto-setup skipped.")
    
    app.run(host="0.0.0.0", port=PORT)
    
