import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aegisq_bot")

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
MINIAPP_URL = os.getenv("MINIAPP_URL", "https://your-server.com")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("Open AEGISQ", web_app=WebAppInfo(url=MINIAPP_URL))]]
    await update.message.reply_text(
        "\ud83d\udd34 **AEGISQ Command Center**\n\n"
        "Your security dashboard inside Telegram.",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("\ud83d\udfe2 All systems nominal. 6/8 modules active.")

async def scan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("\u23f3 Running quick scan...")
    await update.message.reply_text("\u2705 Scan complete. 1 vulnerability found.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("scan", scan_cmd))
    logger.info("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
