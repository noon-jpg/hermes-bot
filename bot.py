import os
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# ======== CONFIG ========
# ستاخذ البيانات من إعدادات السحابة تلقائياً أو يمكنك وضعها هنا مباشرة
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8941078542:AAFa3F22F03oVzBCwrJuhQZN_TnfHtUaNuE
")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "YOUR_OPENROUTER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "nousresearch/hermes-3-llama-3.1-70b"

# رابط موقعك على Render (سيتم وضعه تلقائياً بعد النشر)
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "")
PORT = int(os.environ.get("PORT", 8443))
# =========================

app = Flask(__name__)

# إعداد تطبيق تيليجرام
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
        response.raise_for_status()
        ai_reply = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        ai_reply = f"Sorry, I ran into an error: {e}"

    await update.message.reply_text(ai_reply)

# تسجيل الأوامر
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    """هذه الدالة تستقبل الرسائل القادمة من تيليجرام وتمررها للبوت"""
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    # تشغيل المعالجة بشكل متزامن داخل خادم الـ Web
    import asyncio
    asyncio.run(telegram_app.initialize())
    asyncio.run(telegram_app.process_update(update))
    return "OK", 200

@app.route("/")
def index():
    return "Bot is running on Render!"

if __name__ == "__main__":
    # إعداد الـ Webhook تلقائياً عند تشغيل السيرفر
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/{TELEGRAM_TOKEN}"
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={webhook_url}")
    
    app.run(host="0.0.0.0", port=PORT)
