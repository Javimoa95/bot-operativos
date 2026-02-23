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
def actualizar_contadores(mensaje_id, user_id, estado):
    data = leer_operativos()
    op = data.get(str(mensaje_id))

    if not op:
        return None

    if "asistentes" not in op:
        op["asistentes"] = {}

    anterior = op["asistentes"].get(str(user_id))

    # Si cambia de estado
    if anterior != estado:
        if anterior == "SI":
            op["si"] -= 1
        elif anterior == "NO":
            op["no"] -= 1

        if estado == "SI":
            op["si"] += 1
        elif estado == "NO":
            op["no"] += 1

        op["asistentes"][str(user_id)] = estado

    guardar_operativos(data)
    return op