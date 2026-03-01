import random
import string
from database import conectar
import discord

CATEGORIA_SANCIONES_ID = 1477345672264159342
ROL_SANCIONADOR_ID = 1346520439433728060


def generar_id_unico(cursor):
    while True:
        codigo = "TD-" + ''.join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
        cursor.execute(
            "SELECT id_unico FROM sanciones WHERE id_unico = %s",
            (codigo,)
        )
        if not cursor.fetchone():
            return codigo


def crear_sancion(user_id, nivel, motivo, fecha_limite):
    conn = conectar()
    cursor = conn.cursor()

    id_unico = generar_id_unico(cursor)

    cursor.execute("""
        INSERT INTO sanciones (
            id_unico,
            user_id,
            nivel,
            motivo,
            fecha_limite,
            estado
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (id_unico, user_id, nivel, motivo, fecha_limite, "ABIERTA"))

    conn.commit()
    cursor.close()
    conn.close()

    return id_unico


def actualizar_canal_sancion(id_sancion, canal_id, mensaje_publico_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE sanciones
        SET canal_id = %s,
            mensaje_sancion_id = %s
        WHERE id_unico = %s
    """, (canal_id, mensaje_publico_id, id_sancion))

    conn.commit()
    cursor.close()
    conn.close()


async def crear_canal_sancion(bot, guild, usuario, id_sancion, timestamp, link_mensaje):

    CATEGORIA_SANCIONES_ID = 1477345672264159342
    ROL_SANCIONADOR_ID = 1346520439433728060

    categoria = guild.get_channel(CATEGORIA_SANCIONES_ID)
    rol_sancionador = guild.get_role(ROL_SANCIONADOR_ID)

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        usuario: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        rol_sancionador: discord.PermissionOverwrite(view_channel=True, send_messages=True),
    }

    canal = await guild.create_text_channel(
        name=f"sancion-{usuario.name.lower()}",
        category=categoria,
        overwrites=overwrites
    )

    # 🔔 MENCIÓN ROL Y BORRAR
    aviso = await canal.send(f"{rol_sancionador.mention}")
    await aviso.delete()

    # 📌 MENSAJE PRINCIPAL
    mensaje_principal = await canal.send(
        f"📌 **Sanción ID:** `{id_sancion}`\n\n"
        f"🔗 Mensaje oficial:\n{link_mensaje}\n\n"
        f"👤 Usuario: {usuario.mention}\n\n"
        f"⏳ Fecha límite: <t:{timestamp}:R>"
    )

    await mensaje_principal.pin()

    # ⏳ CONTADOR
    contador = await canal.send(
        f"⏳ Fecha límite: <t:{timestamp}:F>\n"
        f"Tiempo restante: <t:{timestamp}:R>"
    )

    # ⚠️ IMPORTANTE: devolver TODO
    return canal.id, mensaje_principal.id, contador.id

def borrar_sancion(id_sancion):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM sanciones WHERE id_unico = %s",
        (id_sancion,)
    )

    conn.commit()
    cursor.close()
    conn.close()

def obtener_sancion(id_sancion):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM sanciones WHERE id_unico = %s",
        (id_sancion,)
    )

    fila = cursor.fetchone()

    cursor.close()
    conn.close()

    if not fila:
        return None

    # Adaptar a diccionario según tu orden de columnas
    return {
        "id_unico": fila[0],
        "user_id": fila[1],
        "nivel": fila[2],
        "motivo": fila[3],
        "fecha_limite": fila[4],
        "estado": fila[5],
        "canal_id": fila[6],
        "mensaje_sancion_id": fila[7]
    }

def actualizar_contador_mensaje(id_sancion, mensaje_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE sanciones
        SET contador_mensaje_id = %s
        WHERE id_unico = %s
    """, (mensaje_id, id_sancion))

    conn.commit()
    cursor.close()
    conn.close()