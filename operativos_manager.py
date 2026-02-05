import json
import os

ARCHIVO = "operativos.json"

def leer_operativos():
    if not os.path.exists(ARCHIVO):
        return {}

    try:
        with open(ARCHIVO, "r") as f:
            contenido = f.read().strip()
            if not contenido:
                return {}
            return json.loads(contenido)
    except:
        return {}

def guardar_operativos(data):
    with open(ARCHIVO, "w") as f:
        json.dump(data, f, indent=4)

def agregar_operativo(mensaje_id, timestamp, columna):
    data = leer_operativos()
    data[str(mensaje_id)] = {
        "mensaje_id": mensaje_id,
        "timestamp": timestamp,
        "columna": columna,
        "si": 0,
        "no": 0,
        "justificaciones": {}
    }
    guardar_operativos(data)

def obtener_operativo(mensaje_id):
    data = leer_operativos()
    return data.get(str(mensaje_id))

def borrar_operativo(mensaje_id):
    data = leer_operativos()
    if str(mensaje_id) in data:
        del data[str(mensaje_id)]
        guardar_operativos(data)
        return True
    return False
def actualizar_contadores(mensaje_id, user_id, nuevo_estado):
    data = leer_operativos()
    op = data.get(str(mensaje_id))

    if not op:
        return None

    op.setdefault("si", 0)
    op.setdefault("no", 0)
    op.setdefault("usuarios", {})

    user_id = str(user_id)
    estado_anterior = op["usuarios"].get(user_id)

    if estado_anterior == nuevo_estado:
        return op  # ya estaba igual

    if estado_anterior == "SI":
        op["si"] -= 1
    elif estado_anterior == "NO":
        op["no"] -= 1

    if nuevo_estado == "SI":
        op["si"] += 1
    elif nuevo_estado == "NO":
        op["no"] += 1

    op["usuarios"][user_id] = nuevo_estado

    guardar_operativos(data)
    return op  # 👈 IMPORTANTE
