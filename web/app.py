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
from datetime import datetime
import io
import pandas as pd
from fastapi.responses import StreamingResponse

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



def obtener_movimientos_recientes():

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT username, tipo, objeto_nombre, cantidad, almacen, timestamp
        FROM armamento_logs
        ORDER BY timestamp DESC
        LIMIT 20
    """)

    movimientos = cur.fetchall()

    for m in movimientos:
        m["fecha"] = datetime.fromtimestamp(m["timestamp"]).strftime("%d/%m %H:%M")

    cur.close()
    conn.close()

    return movimientos

def obtener_ranking_armamento():

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT username, SUM(cantidad) AS total
        FROM armamento_logs
        WHERE tipo = 'sacado'
        GROUP BY username
        ORDER BY total DESC
        LIMIT 10
    """)

    ranking = cur.fetchall()

    cur.close()
    conn.close()

    return ranking



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
    movimientos = obtener_movimientos_recientes()
    ranking = obtener_ranking_armamento()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "stats": stats,
            "movimientos": movimientos,
            "ranking": ranking,
            "page": "dashboard"
        }
    )

@app.get("/operativos", response_class=HTMLResponse)
async def operativos(request: Request):

    user = request.session.get("user")

    if not user:
        return RedirectResponse("/")

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT mensaje_id, timestamp, columna, procesado
        FROM operativos
        ORDER BY timestamp DESC
    """)
    operativos = cur.fetchall()
    for o in operativos:
        if o["timestamp"]:
            o["fecha"] = datetime.fromtimestamp(o["timestamp"]).strftime("%d/%m/%Y %H:%M")
        else:
            o["fecha"] = "-"
    cur.close()
    conn.close()

    return templates.TemplateResponse(
        "operativos.html",
        {
            "request": request,
            "user": user,
            "operativos": operativos
        }
    )

@app.get("/sanciones", response_class=HTMLResponse)
async def sanciones(request: Request):

    user = request.session.get("user")

    if not user:
        return RedirectResponse("/")

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT id_unico, user_id, nivel, motivo, fecha_limite, estado
        FROM sanciones
        ORDER BY fecha_limite DESC
    """)

    sanciones = cur.fetchall()

    for s in sanciones:
        if s["fecha_limite"]:
            s["fecha"] = datetime.fromtimestamp(s["fecha_limite"]).strftime("%d/%m/%Y %H:%M")
        else:
            s["fecha"] = "-"

    cur.close()
    conn.close()
    
    return templates.TemplateResponse(
        "sanciones.html",
        {
            "request": request,
            "user": user,
            "sanciones": sanciones
        }
    )

@app.get("/armamento", response_class=HTMLResponse)
async def armamento(request: Request, page: int = 1, usuario: str = "", tipo: str = ""):

    user = request.session.get("user")

    if not user:
        return RedirectResponse("/")

    limit = 20
    offset = (page - 1) * limit

    conn = conectar()
    cur = conn.cursor()

    query = """
        SELECT username, tipo, objeto_nombre, cantidad, almacen, timestamp
        FROM armamento_logs
        WHERE 1=1
    """

    params = []

    if usuario:
        query += " AND username ILIKE %s"
        params.append(f"%{usuario}%")

    if tipo:
        query += " AND tipo = %s"
        params.append(tipo)

    query += " ORDER BY timestamp DESC LIMIT %s OFFSET %s"

    params.append(limit)
    params.append(offset)

    cur.execute(query, params)

    movimientos = cur.fetchall()

    for m in movimientos:
        m["fecha"] = datetime.fromtimestamp(m["timestamp"]).strftime("%d/%m %H:%M")

    cur.close()
    conn.close()

    return templates.TemplateResponse(
        "armamento.html",
        {
            "request": request,
            "user": user,
            "movimientos": movimientos,
            "page": page,
            "usuario": usuario,
            "tipo": tipo
        }
    )
    
@app.get("/armamento/export")
async def exportar_armamento(request: Request):

    user = request.session.get("user")

    if not user:
        return RedirectResponse("/")

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT
        username AS usuario,
        tipo,
        objeto_nombre AS objeto,
        cantidad,
        almacen,
        to_char(to_timestamp(timestamp), 'YYYY-MM-DD HH24:MI') AS fecha
        FROM armamento_logs
        ORDER BY timestamp DESC
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    df = pd.DataFrame(rows)
    
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Armamento")

    output.seek(0)

    headers = {
        "Content-Disposition": "attachment; filename=armamento_logs.xlsx"
    }

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )