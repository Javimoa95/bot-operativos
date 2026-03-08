import threading
import uvicorn
import os

from bot.main import bot, BOT_TOKEN


def run_bot():
    bot.run(BOT_TOKEN)


def run_web():
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("web.app:app", host="0.0.0.0", port=port)


bot_thread = threading.Thread(target=run_bot)
bot_thread.start()

run_web()