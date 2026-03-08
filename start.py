import threading
import uvicorn
import os

from bot.main import bot, BOT_TOKEN


def start_bot():
    bot.run(BOT_TOKEN)


if __name__ == "__main__":
    print("🚀 START.PY EJECUTÁNDOSE")

    threading.Thread(target=start_bot, daemon=True).start()

    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        "web.app:app",
        host="0.0.0.0",
        port=port
    )