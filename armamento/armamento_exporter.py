import json
from datetime import datetime, timedelta
import pytz
from database import conectar

CANAL_EXPORTES_ARMAMENTO_ID = 1343251332152168579

# -----------------------------------------------------

def obtener_semana_actual():
    tz = pytz.timezone("Europe/Madrid")
    ahora = datetime.now(tz)
    return ahora.isocalendar()[1]

def obtener_rango_semana():
    tz = pytz.timezone("Europe/Madrid")
    ahora = datetime.now(tz)

    inicio = ahora - timedelta(days=ahora.weekday())
    fin = inicio + timedelta(days=6)

    inicio_str = inicio.strftime("%d/%m")
    fin_str = fin.strftime("%d/%m")

    return inicio_str, fin_str

# -----------------------------------------------------

def obtener_ultima_semana_exportada():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT ultima_semana FROM armamento_control WHERE id = 1")
    row = cursor.fetchone()

    conn.close()

    if row:
        return row["ultima_semana"]
    return None

def actualizar_semana_exportada(semana):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO armamento_control (id, ultima_semana)
        VALUES (1, ?)
    """, (semana,))

    conn.commit()
    conn.close()

# -----------------------------------------------------

def generar_json_semana():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM armamento_logs")
    rows = cursor.fetchall()

    usuarios = {}

    for row in rows:

        if row["categoria"] != "arma":
            continue

        user_id = row["user_id"]
        username = row["username"]
        tipo = row["tipo"]
        cantidad = row["cantidad"]

        if user_id not in usuarios:
            usuarios[user_id] = {
                "username": username,
                "metido": 0,
                "sacado": 0
            }

        usuarios[user_id][tipo] += cantidad

    inicio_str, fin_str = obtener_rango_semana()

    data_final = {
        "semana": f"{inicio_str} - {fin_str}",
        "usuarios": {}
    }

    for data in usuarios.values():
        balance = data["metido"] - data["sacado"]

        data_final["usuarios"][data["username"]] = {
            "metido": data["metido"],
            "sacado": data["sacado"],
            "balance": balance
        }

    nombre_archivo = f"logs semana {inicio_str} a {fin_str}.json"

    with open(nombre_archivo, "w", encoding="utf-8") as f:
        json.dump(data_final, f, indent=4, ensure_ascii=False)

    conn.close()

    return nombre_archivo, obtener_semana_actual()

# -----------------------------------------------------

def mover_a_historial(semana):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO armamento_logs_historial (
            message_id, user_id, username, tipo,
            categoria, objeto_nombre, objeto_codigo,
            cantidad, almacen, timestamp, semana
        )
        SELECT message_id, user_id, username, tipo,
               categoria, objeto_nombre, objeto_codigo,
               cantidad, almacen, timestamp, ?
        FROM armamento_logs
    """, (semana,))

    cursor.execute("DELETE FROM armamento_logs")

    conn.commit()
    conn.close()