import threading
import uvicorn
import os

from bot.main import bot, BOT_TOKEN


def start_bot():
    bot.run(BOT_TOKEN)


# arrancar bot en segundo plano
threading.Thread(target=start_bot, daemon=True).start()

# puerto que usa Railway
port = int(os.environ.get("PORT", 8000))

# arrancar web
uvicorn.run(
    "web.app:app",
    host="0.0.0.0",
    port=port
)