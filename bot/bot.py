"""AEGISQ Telegram Bot Bridge."""
import os, json, logging, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger("aegisq-bot")

TOKEN = os.getenv("BOT_TOKEN", "")
DETECTOR_URL = os.getenv("DETECTOR_URL", "http://detector:8000")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))

def restricted(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if ALLOWED_USER_ID and update.effective_user.id != ALLOWED_USER_ID:
            await update.message.reply_text("⛔ Unauthorized")
            return
        return await func(update, context)
    return wrapper

async def fetch_detector(path: str):
    import httpx
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{DETECTOR_URL}{path}", timeout=30)
            return r.json()
        except Exception as e:
            return {"error": str(e)}

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🖥 Dashboard", web_app={"url": os.getenv("MINIAPP_URL", "https://aegisq-miniapp.vercel.app")})],
        [InlineKeyboardButton("📊 Run Detection", callback_data="detect"),
         InlineKeyboardButton("📋 Latest Report", callback_data="report")]
    ]
    await update.message.reply_text(
        "🤖 *AEGISQ — Quantum-Ready AI Threat Detection*

"
        "Your security command center. Use the buttons below or mini app.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

@restricted
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "detect":
        await query.edit_message_text("🔍 Running detection pipeline...")
        result = await fetch_detector("/report")
        if "error" in result:
            await query.edit_message_text(f"❌ Error: {result['error']}")
        else:
            msg = (
                f"📊 *Detection Report*
"
                f"• Flows: `{result.get('total_flows', '?')}`
"
                f"• Alerts: `{result.get('alerts_raised', '?')}`
"
                f"• Detection Rate: `{result.get('detection_rate', '?')}%`
"
                f"• False Positives: `{result.get('false_positives', '?')}`
"
            )
            by_sev = result.get("by_severity", {})
            if by_sev:
                msg += "
*By Severity:*
"
                for s, c in by_sev.items():
                    icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}.get(s, "⚪")
                    msg += f"{icon} {s}: `{c}`
"
            await query.edit_message_text(msg, parse_mode="Markdown")
    elif query.data == "report":
        result = await fetch_detector("/report")
        if "error" in result:
            await query.edit_message_text(f"❌ Error: {result['error']}")
        else:
            await query.edit_message_text(
                f"📋 *Latest Report*
```\n{json.dumps(result, indent=2)[:2000]}\n```",
                parse_mode="Markdown"
            )

def main():
    if not TOKEN:
        logger.error("BOT_TOKEN not set")
        return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    logger.info("Bot polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
