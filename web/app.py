from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from web.oauth import get_login_url, exchange_code, get_user
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from bot.database import conectar


app = FastAPI()

app.mount("/static", StaticFiles(directory="web/static"), name="static")
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")
templates = Jinja2Templates(directory="web/templates")
import threading
from bot.main import bot, BOT_TOKEN

def start_bot():
    bot.run(BOT_TOKEN)

@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=start_bot)
    thread.daemon = True
    thread.start()


def obtener_stats():

    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS total FROM sanciones")
    sanciones = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM operativos")
    operativos = cur.fetchone()["total"]

    cur.close()
    conn.close()

    return {
        "sanciones": sanciones,
        "operativos": operativos
    }


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login")
async def login():
    return RedirectResponse(get_login_url())

@app.get("/callback")
async def callback(request: Request, code: str):

    token_data = exchange_code(code)
    access_token = token_data["access_token"]

    user = get_user(access_token)

    request.session["user"] = user

    return RedirectResponse("/dashboard")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):

    user = request.session.get("user")

    if not user:
        return RedirectResponse("/")

    stats = obtener_stats()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "stats": stats
        }
    )