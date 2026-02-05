import os
BOT_TOKEN = os.getenv("BOT_TOKEN")

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import pytz
from sheets_manager import (
    conectar_sheet,
    obtener_o_crear_fila,
    crear_columna_operativo,
    escribir_asistencia_operativo,
    actualizar_total,
    borrar_columna_operativo,
    recalcular_totales_global
)
from operativos_manager import (
    agregar_operativo,
    obtener_operativo,
    borrar_operativo,
    leer_operativos,
    guardar_operativos,
    actualizar_contadores
)

sheet = conectar_sheet()
print("📊 Conectado a Google Sheets")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
GUILD_ID = 1204813117108916304  # <-- ID de tu servidor

ROL_OBJETIVO_ID = 1263582833218158652  # <-- PON AQUÍ EL ID DEL ROL
ROL_ADMIN_ID = 1345432524314251306  # <-- ID del rol que puede usar /operativo
ROL_AVISO_ID = 1263582833218158652  # <-- ID del rol que se menciona siempre
CANAL_LOGS_ID = 1205530911991406693


async def load_cogs():
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            await bot.load_extension(f"cogs.{file[:-3]}")

async def log_justificacion(interaction, operativo_id, motivo):
    canal_logs = interaction.guild.get_channel(CANAL_LOGS_ID)
    if not canal_logs:
        return

    data = leer_operativos()
    op = data.get(str(operativo_id))

    user_id = str(interaction.user.id)
    link_operativo = f"https://discord.com/channels/{interaction.guild.id}/{interaction.channel.id}/{operativo_id}"

    texto = (
        f"**Justificación de ausencia**\n"
        f"Usuario: {interaction.user.mention}\n"
        f"Operativo: {link_operativo}\n"
        f"Motivo: {motivo}"
    )

    if user_id in op["justificaciones"]:
        # EDITAR
        mensaje_id = op["justificaciones"][user_id]
        try:
            mensaje = await canal_logs.fetch_message(mensaje_id)
            await mensaje.edit(content=texto)
        except:
            nuevo = await canal_logs.send(texto)
            op["justificaciones"][user_id] = nuevo.id
    else:
        # CREAR
        nuevo = await canal_logs.send(texto)
        op["justificaciones"][user_id] = nuevo.id

    guardar_operativos(data)


async def editar_contadores_mensaje(interaction, op):
    si = op.get("si", 0)
    no = op.get("no", 0)

    canal = interaction.channel
    mensaje = await canal.fetch_message(op["mensaje_id"])

    texto_original = mensaje.content

    if "**Asistencias en vivo**" in texto_original:
        texto_original = texto_original.split("**Asistencias en vivo**")[0]

    nuevo_texto = (
        texto_original.strip() +
        f"\n\n**Asistencias en vivo**\nSI: {si}\nNO: {no}"
    )

    await mensaje.edit(content=nuevo_texto)


def crear_timestamps(fecha_str, hora_str):
    tz = pytz.timezone("Europe/Madrid")

    dia, mes = map(int, fecha_str.split("/"))
    h, m = map(int, hora_str.split(":"))

    ahora = datetime.now(tz)
    anio = ahora.year

    fecha_naive = datetime(anio, mes, dia, h, m)
    fecha_operativo = tz.localize(fecha_naive)

    timestamp_operativo = int(fecha_operativo.timestamp())
    timestamp_sede = int((fecha_operativo - timedelta(minutes=15)).timestamp())

    return timestamp_operativo, timestamp_sede

# -------- FECHA HORA --------
def obtener_fecha_hora():
    tz = pytz.timezone("Europe/Madrid")
    ahora = datetime.now(tz)

    dias = {
        "Monday": "Lunes",
        "Tuesday": "Martes",
        "Wednesday": "Miércoles",
        "Thursday": "Jueves",
        "Friday": "Viernes",
        "Saturday": "Sábado",
        "Sunday": "Domingo"
    }

    dia = dias[ahora.strftime("%A")]
    hora = ahora.strftime("%H:%M")

    return dia, hora

# -------- MODAL --------
class JustificacionModal(discord.ui.Modal):
    def __init__(self, mensaje_id):
        super().__init__(title="Justificación de ausencia")
        self.mensaje_id = mensaje_id

    motivo = discord.ui.TextInput(
        label="Escribe tu justificación",
        style=discord.TextStyle.long,
        required=True,
        max_length=300
    )

    async def on_submit(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        op = obtener_operativo(self.mensaje_id)
        columna = op["columna"]

        fila = obtener_o_crear_fila(sheet, interaction.user.id, str(interaction.user))
        dia, hora = obtener_fecha_hora()

        escribir_asistencia_operativo(
            sheet,
            fila,
            columna,
            "NO",
            hora,
            self.motivo.value
        )

        op = actualizar_contadores(self.mensaje_id, interaction.user.id, "NO")
        await editar_contadores_mensaje(interaction, op)
        await log_justificacion(interaction, self.mensaje_id, self.motivo.value)
        await interaction.followup.send(
            "✅ Justificación enviada correctamente",
            ephemeral=True
        )


# -------- BOTONES --------
class OperativoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Asisto", style=discord.ButtonStyle.success)
    async def asistir(self, interaction: discord.Interaction, button: discord.ui.Button):
    
        await interaction.response.defer(ephemeral=True)
    
        import time
    
        op = obtener_operativo(interaction.message.id)  # ← AQUÍ VA
    
        if not op:
            await interaction.followup.send("⛔ Operativo inválido.", ephemeral=True)
            return
    
        if time.time() > op["timestamp"]:
            await interaction.followup.send("⛔ Operativo cerrado.", ephemeral=True)
            return
    
        member = await interaction.guild.fetch_member(interaction.user.id)
    
        if not any(rol.id == ROL_OBJETIVO_ID for rol in member.roles):
            await interaction.followup.send("⛔ No tienes el rol necesario.", ephemeral=True)
            return
    
        fila = obtener_o_crear_fila(sheet, interaction.user.id, str(interaction.user))
    
        columna = op["columna"]
        dia, hora = obtener_fecha_hora()
    
        escribir_asistencia_operativo(sheet, fila, columna, "SI", hora)
        actualizar_total(sheet, fila)
    
        op = actualizar_contadores(interaction.message.id, interaction.user.id, "SI")
        await editar_contadores_mensaje(interaction, op)
    
        await interaction.followup.send("✔ Asistencia registrada", ephemeral=True)
    @discord.ui.button(label="No asisto", style=discord.ButtonStyle.danger)
    async def no_asistir(self, interaction: discord.Interaction, button: discord.ui.Button):
        import time

        op = obtener_operativo(interaction.message.id)
        member = await interaction.guild.fetch_member(interaction.user.id)


        if not member:
            await interaction.followup.send("Error obteniendo usuario.", ephemeral=True)
            return

        if not op:
            await interaction.response.send_message(
                "⛔ Operativo inválido.",
                ephemeral=True
            )
            return

        if time.time() > op["timestamp"]:
            await interaction.response.send_message(
                "⛔ Operativo cerrado.",
                ephemeral=True
            )
            return


        if not any(rol.id == ROL_OBJETIVO_ID for rol in member.roles):
            await interaction.response.send_message(
                "⛔ No tienes el rol necesario.",
                ephemeral=True
            )
            return

        modal = JustificacionModal(interaction.message.id)
        await interaction.response.send_modal(modal)

# -------- READY --------
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)

    bot.tree.clear_commands(guild=guild)
    await bot.tree.sync(guild=guild)
    await bot.tree.sync()
    print(f"✅ Bot conectado como {bot.user}")

# -------- SLASH --------
@bot.tree.command(name="operativo", description="Crear operativo automático")
@app_commands.describe(
    fecha="Fecha DD/MM",
    hora="Hora HH:MM",
    descripcion="Descripción del operativo",
    encargado="Usuario que lo llevará",
)
async def operativo(
    interaction: discord.Interaction,
    fecha: str,
    hora: str,
    descripcion: str,
    encargado: discord.Member,
):
    rol_aviso = interaction.guild.get_role(ROL_AVISO_ID)

    # ----- PERMISOS -----
    member = await interaction.guild.fetch_member(interaction.user.id)

    if not any(rol.id == ROL_ADMIN_ID for rol in member.roles):
        await interaction.response.send_message(
            "⛔ No tienes permiso para usar este comando.",
            ephemeral=True
        )
        return

    # ----- TIMESTAMPS -----
    try:
        ts_operativo, ts_sede = crear_timestamps(fecha, hora)
    except:
        await interaction.response.send_message(
            "❌ Formato inválido. Usa DD/MM y HH:MM",
            ephemeral=True
        )
        return
    columna_operativo = crear_columna_operativo(sheet, fecha)

    # ----- MENSAJE -----
    texto_operativo = (
        f"# OPERATIVO DIA {fecha}\n\n"
        f"**Hora del operativo:** <t:{ts_operativo}:t>\n\n"
        f"**Hora para estar en sede:** <t:{ts_sede}:t>\n\n"
        f"**El operativo consistirá en:** {descripcion}\n\n"
        f"**El operativo lo llevará:** {encargado.mention}\n\n"
        f"Es obligatorio marcar asistencia con un **ASISTO** o **NO ASISTO**\n\n"
        f"En caso de no poder asistir se debe justificar\n"
        f"mediante el bot\n\n"
        f"Si no se justifica, si marcas que sí y no asistes, si no marcas se le sancionará. {rol_aviso.mention}"
    )

    # ----- ENVIAR MENSAJE -----
    mensaje_enviado = await interaction.channel.send(
        texto_operativo,
        view=OperativoView()
    )
    agregar_operativo(
        mensaje_enviado.id,
        ts_operativo,
        columna_operativo,
)

    await interaction.response.send_message(
        "✅ Operativo creado correctamente.",
        ephemeral=True
    )

@bot.tree.command(name="borrarop", description="Borrar operativo")
@app_commands.describe(link="Link del mensaje del operativo")
async def borrarop(interaction: discord.Interaction, link: str):

    member = await interaction.guild.fetch_member(interaction.user.id)

    if not any(rol.id == ROL_ADMIN_ID for rol in member.roles):
        await interaction.response.send_message(
            "⛔ No tienes permiso.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    partes = link.split("/")
    mensaje_id = int(partes[-1])
    
    data = leer_operativos()
    op = data.get(str(mensaje_id))

    # BORRAR MENSAJE
    try:
        mensaje = await interaction.channel.fetch_message(mensaje_id)
        await mensaje.delete()
    except:
        pass  # si ya no existe no pasa nada

    if op and "columna" in op:
        borrar_columna_operativo(sheet, op["columna"])
        recalcular_totales_global(sheet)
    # BORRAR JSON
    if borrar_operativo(mensaje_id):
        await interaction.followup.send(
            "🗑 Operativo eliminado correctamente.",
            ephemeral=True
        )
    else:
        await interaction.followup.send(
            "⚠ No se encontró operativo.",
            ephemeral=True
        )


bot.run(BOT_TOKEN)