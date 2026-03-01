import re

pattern = re.compile(
    r"ha (metido|sacado) x([\d\.]+) (.+?) \((.+?)\).*?'(.+?)'"
)

def parsear_mensaje(message):

    if not message.mentions:
        return None

    match = pattern.search(message.content)
    if not match:
        return None

    tipo = match.group(1)
    cantidad = int(match.group(2).replace(".", ""))
    objeto_nombre = match.group(3).strip()
    objeto_codigo = match.group(4).strip()
    almacen = match.group(5).strip()

    usuario = message.mentions[0]

    categoria = detectar_categoria(objeto_codigo)

    return {
        "message_id": message.id,
        "user_id": usuario.id,
        "username": usuario.display_name,
        "tipo": tipo,
        "categoria": categoria,
        "objeto_nombre": objeto_nombre,
        "objeto_codigo": objeto_codigo,
        "cantidad": cantidad,
        "almacen": almacen,
        "timestamp": int(message.created_at.timestamp())
    }


def detectar_categoria(codigo):

    if codigo.startswith("WEAPON_"):
        return "arma"

    if codigo.startswith("ammo-"):
        return "municion"

    if codigo == "money":
        return "dinero"

    if codigo.startswith("weed") or codigo in ["cocaina", "amapola", "peyote"]:
        return "sustancia"

    if codigo in [
        "sandwich", "water", "turron", "polvoron",
        "ballbarry_cupcake", "fingle_burger"
    ]:
        return "comida"

    if codigo.startswith("at_"):
        return "accesorio"

    return "objeto"