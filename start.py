import threading
import uvicorn
import os

from bot.main import bot, BOT_TOKEN


def run_bot():
    bot.run(BOT_TOKEN)


# lanzar bot en segundo plano
bot_thread = threading.Thread(target=run_bot)
bot_thread.start()

# puerto que Railway asigna automáticamente
port = int(os.environ.get("PORT", 8000))

# arrancar servidor web
uvicorn.run(
    "web.app:app",
    host="0.0.0.0",
    port=port,
    log_level="info"
)