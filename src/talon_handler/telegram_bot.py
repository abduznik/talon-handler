import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from .config import ConfigManager

# Disable verbose logging from library
logging.getLogger("httpx").setLevel(logging.WARNING)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Binds the chat_id using the Ghost Auth OTP."""
    config = ConfigManager()
    
    if not context.args:
        await update.message.reply_text("Please provide the 6-digit auth code: /start <CODE>")
        return

    user_code = context.args[0]
    pending_otp = config.data.get("pending_otp")

    if pending_otp and user_code == pending_otp:
        config.data["chat_id"] = update.effective_chat.id
        config.data.pop("pending_otp", None)
        config.save()
        await update.message.reply_text("✅ Talon Ghost Auth successful. Your Chat ID is now bound for alerts.")
    else:
        await update.message.reply_text("❌ Invalid or expired auth code.")

class TalonBot:
    def __init__(self, token: str):
        self.application = ApplicationBuilder().token(token).build()
        self.application.add_handler(CommandHandler("start", start))

    async def run(self):
        """Runs the bot polling."""
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
    async def stop(self):
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()

async def send_telegram_alert(token: str, chat_id: int, message: str):
    """Sends a one-off alert message."""
    from telegram import Bot
    bot = Bot(token=token)
    async with bot:
        await bot.send_message(chat_id=chat_id, text=message)
