import threading
import uvicorn
from bot.main import bot, BOT_TOKEN


def run_bot():
    bot.run(BOT_TOKEN)


def run_web():
    uvicorn.run("web.app:app", host="0.0.0.0", port=8000)


bot_thread = threading.Thread(target=run_bot)
bot_thread.start()

run_web()