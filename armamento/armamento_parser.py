import re

pattern = re.compile(
    r"ha\s+(metido|sacado)\s+x([\d\.]+)\s+(.+?)\s+\(`(.+?)`\)\s+.*?'(.+?)'",
    re.IGNORECASE
)

def parsear_mensaje(message):

    match = pattern.search(message.content)
    if not match:
        return None

    tipo = match.group(1).lower()
    cantidad = int(match.group(2).replace(".", ""))
    objeto_nombre = match.group(3).strip()
    objeto_codigo = match.group(4).strip()
    almacen = match.group(5).strip()

    # 🔹 Extraer ID real del usuario desde <@123456789>
    match_id = re.search(r"<@(\d+)>", message.content)
    if not match_id:
        return None

    user_id = int(match_id.group(1))

    categoria = detectar_categoria(objeto_codigo)

    return {
        "message_id": message.id,
        "user_id": user_id,
        "username": None,  # ya no dependemos del nombre
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


def obtener_categoria(objeto_codigo):

    if objeto_codigo.startswith("WEAPON_"):
        return "armas"

    if objeto_codigo.startswith("ammo"):
        return "municion"

    if objeto_codigo in ["chaleco", "at_suppressor_light", "at_scope_holo", "at_flashlight"]:
        return "equipamiento"

    if objeto_codigo in ["water", "beer", "sandwich", "fingle_burger", "turron", "polvoron"]:
        return "comida"

    if objeto_codigo in ["weed_amnesia", "weed_amnesiapack", "weed_purplepack", "cocaina"]:
        return "drogas"

    return "otros"