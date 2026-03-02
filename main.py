import os
BOT_TOKEN = os.getenv("BOT_TOKEN")
from discord.ext import tasks
import asyncio
import time
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import pytz
from database import inicializar_db
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
    actualizar_contadores,
    obtener_operativos_pendientes,
    marcar_operativo_procesado,
    marcar_recordatorio_enviado
)

sheet = conectar_sheet()
print("📊 Conectado a Google Sheets")
inicializar_db()
print("🗄 Base de datos inicializada")
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
GUILD_ID = 1204813117108916304  # <-- ID de tu servidor

ROL_OBJETIVO_ID = 1263582833218158652  # <-- PON AQUÍ EL ID DEL ROL
ROL_ADMIN_ID = 1345432524314251306  # <-- ID del rol que puede usar /operativo
ROL_AVISO_ID = 1263582833218158652  # <-- ID del rol que se menciona siempre
CANAL_LOGS_ID = 1205530911991406693
CANAL_ESTADO_BOT_ID = 1204823850274263140  # <-- PON TU ID
mensaje_estado_bot = None
async def load_cogs():

    # Cargar cogs normales
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            await bot.load_extension(f"cogs.{file[:-3]}")

    # Cargar cogs de armamento
    for file in os.listdir("./armamento"):
        if file.endswith(".py") and file.endswith("_cog.py"):
            await bot.load_extension(f"armamento.{file[:-3]}")


async def log_justificacion(interaction, operativo_id, motivo):
    canal_logs = interaction.guild.get_channel(CANAL_LOGS_ID)
    if not canal_logs:
        return

    from operativos_manager import (
        obtener_justificacion,
        guardar_justificacion
    )

    user_id = interaction.user.id

    link_operativo = (
        f"https://discord.com/channels/"
        f"{interaction.guild.id}/"
        f"{interaction.channel.id}/"
        f"{operativo_id}"
    )

    texto = (
        f"**Justificación de ausencia**\n"
        f"Usuario: {interaction.user.mention}\n"
        f"Operativo: {link_operativo}\n"
        f"Motivo: {motivo}"
    )

    mensaje_existente_id = obtener_justificacion(operativo_id, user_id)

    if mensaje_existente_id:
        try:
            mensaje = await canal_logs.fetch_message(mensaje_existente_id)
            await mensaje.edit(content=texto)
            return
        except:
            pass

    nuevo = await canal_logs.send(texto)
    guardar_justificacion(operativo_id, user_id, nuevo.id)


async def editar_contadores_mensaje(interaction, op):
    si = op.get("si", 0)
    no = op.get("no", 0)

    asistentes = op.get("asistentes", {})

    lista_si = []
    lista_no = []

    for user_id, estado in asistentes.items():
        if estado == "SI":
            lista_si.append(f"<@{user_id}>")
        elif estado == "NO":
            lista_no.append(f"<@{user_id}>")

    texto_si = "\n".join(lista_si) if lista_si else "Nadie"
    texto_no = "\n".join(lista_no) if lista_no else "Nadie"

    canal = interaction.channel
    mensaje = await canal.fetch_message(op["mensaje_id"])

    texto_original = mensaje.content

    if "**Asistencias en vivo**" in texto_original:
        texto_original = texto_original.split("**Asistencias en vivo**")[0]

    nuevo_texto = (
        texto_original.strip() +
        f"\n\n**Asistencias en vivo**\n"
        f"SI: {si}\n"
        f"NO: {no}\n\n"
        f"**ASISTEN:**\n{texto_si}\n\n"
        f"**NO ASISTEN:**\n{texto_no}"
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

    @discord.ui.button(
        label="Asisto",
        style=discord.ButtonStyle.success,
        custom_id="operativo_asisto"
    )
    async def asistir(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer(ephemeral=True)

        import time

        op = obtener_operativo(interaction.message.id)

        if not op:
            await interaction.followup.send("⛔ Operativo inválido.", ephemeral=True)
            return

        if int(time.time()) > int(op["timestamp"]):
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

    @discord.ui.button(
        label="No asisto",
        style=discord.ButtonStyle.danger,
        custom_id="operativo_no_asisto"
    )
    async def no_asistir(self, interaction: discord.Interaction, button: discord.ui.Button):

        import time

        op = obtener_operativo(interaction.message.id)
        member = await interaction.guild.fetch_member(interaction.user.id)

        if not op:
            await interaction.followup.send("⛔ Operativo inválido.", ephemeral=True)
            return

        if int(time.time()) > int(op["timestamp"]):
            await interaction.followup.send("⛔ Operativo cerrado.", ephemeral=True)
            return

        if not any(rol.id == ROL_OBJETIVO_ID for rol in member.roles):
            await interaction.followup.send("⛔ No tienes el rol necesario.", ephemeral=True)
            return

        modal = JustificacionModal(interaction.message.id)
        await interaction.response.send_modal(modal)
        
# -------- READY --------
@bot.event
async def setup_hook():
    await load_cogs()

@bot.event
async def on_ready():

    global mensaje_estado_bot

    canal_estado = bot.get_channel(CANAL_ESTADO_BOT_ID)

    if canal_estado:

        # Enviar mensaje temporal
        mensaje_estado_bot = await canal_estado.send(
            "⚠ **El bot se está actualizando...**\n"
            "Por favor no interactuéis hasta que termine."
        )

    # ---- TU CÓDIGO ACTUAL ----
    guild = discord.Object(id=GUILD_ID)

    if not revisar_operativos.is_running():
        revisar_operativos.start()

    bot.tree.clear_commands(guild=guild)
    await bot.tree.sync(guild=guild)
    await bot.tree.sync()
    bot.add_view(OperativoView())

    print(f"✅ Bot conectado como {bot.user}")

    # ---- MENSAJE FINAL ----
    if mensaje_estado_bot:
        await mensaje_estado_bot.edit(
            content="✅ **Bot actualizado correctamente.**\n"
                    "Ya podéis usarlo con normalidad."
        )

        # Opcional: borrar tras 10 segundos
        await asyncio.sleep(10)
        await mensaje_estado_bot.delete()

@tasks.loop(seconds=60)
async def revisar_operativos():

    ahora = int(time.time())
    operativos = obtener_operativos_pendientes()
    print("======== LOOP REVISAR OPERATIVOS ========")
    print("OPERATIVOS:", operativos)

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return

    rol = guild.get_role(ROL_OBJETIVO_ID)
    if not rol:
        return

    for mensaje_id, timestamp, columna, procesado, recordatorio_enviado in operativos:

        timestamp = int(timestamp)

        # ---------------- RECORDATORIO 2H ----------------
        if not recordatorio_enviado:

            tiempo_restante = timestamp - ahora

            if 0 < tiempo_restante <= 7200:

                op = obtener_operativo(mensaje_id)
                if not op:
                    continue

                asistentes = op.get("asistentes", {})

                for member in rol.members:
                    if str(member.id) not in asistentes:
                        try:
                            await member.send(
                                "⏰ Recordatorio de operativo\n\n"
                                "No has marcado asistencia todavía.\n\n"
                                "Si no marcas, se generará sanción automática."
                            )
                        except:
                            pass

                marcar_recordatorio_enviado(mensaje_id)

        # ---------------- CIERRE AUTOMÁTICO ----------------
        if ahora >= timestamp and not procesado:

            op = obtener_operativo(mensaje_id)
            if not op:
                continue

            asistentes = op.get("asistentes", {})

            canal_publico = bot.get_channel(1220866157649727489)
            if not canal_publico:
                continue

            for member in rol.members:

                # 🔥 SI YA MARCÓ → NO SANCIONAR
                if str(member.id) in asistentes:
                    continue

                from sanciones_manager import (
                    crear_sancion,
                    crear_canal_sancion,
                    actualizar_canal_sancion
                )

                fecha_limite = ahora + (3 * 24 * 60 * 60)

                id_sancion = crear_sancion(
                    member.id,
                    5,
                    "no marcar operativo",
                    fecha_limite
                )

                mensaje_publico = await canal_publico.send(
                    f"**SANCION NIVEL 5 ARMAMENTISTICA :**\n\n"
                    f"**ID Sanción:** `{id_sancion}`\n\n"
                    f"Tienes 1 aviso y debes de entregar: **5 pipas**\n\n"
                    f"**Fecha limite:** <t:{fecha_limite}:d>\n\n"
                    f"**Usuario sancionado:** {member.mention}\n\n"
                    f"**Motivo:** no marcar operativo\n\n"
                    f"Cualquier duda o fallo abre ticket.\n"
                    f"Si cumples la sancion abre ticket con las pruebas y tagueame."
                )

                link_mensaje = mensaje_publico.jump_url

                canal_id, mensaje_privado_id, contador_id = await crear_canal_sancion(
                    bot,
                    guild,
                    member,
                    id_sancion,
                    fecha_limite,
                    link_mensaje
                )

                actualizar_canal_sancion(
                    id_sancion,
                    canal_id,
                    mensaje_privado_id,
                    mensaje_publico.id,
                    contador_id
                )

            # -------- MENSAJE FINAL EN OPERATIVO --------
            try:
                canal_operativo = guild.get_channel(operativos[0][0])
                mensaje_operativo = await canal_publico.fetch_message(mensaje_id)

                no_marcaron = [
                    member.mention
                    for member in rol.members
                    if str(member.id) not in asistentes
                ]

                if no_marcaron:
                    texto = (
                        "Operativo finalizado.\n\n"
                        "No marcaron asistencia:\n" +
                        "\n".join(no_marcaron)
                    )
                else:
                    texto = "Operativo finalizado.\n\nTodos marcaron asistencia."

                await mensaje_operativo.reply(texto)

            except:
                pass

            marcar_operativo_procesado(mensaje_id)

# -------- SLASH --------
@bot.tree.command(name="discordid", description="Muestra tu ID de Discord")
async def discordid(interaction: discord.Interaction):

    await interaction.response.send_message(
        f"🆔 Tu ID de Discord es:\n`{interaction.user.id}`",
        ephemeral=True
    )

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
    await interaction.response.defer(ephemeral=True)
    rol_aviso = interaction.guild.get_role(ROL_AVISO_ID)

    # ----- PERMISOS -----
    member = await interaction.guild.fetch_member(interaction.user.id)

    if not any(rol.id == ROL_ADMIN_ID for rol in member.roles):
        await interaction.followup.send(
            "⛔ No tienes permiso para usar este comando.",
            ephemeral=True
        )
        return

    # ----- TIMESTAMPS -----
    try:
        ts_operativo, ts_sede = crear_timestamps(fecha, hora)
    except:
        await interaction.followup.send(
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
    # -----------------------------
    # 📩 DM AUTOMÁTICO AL CREAR
    # -----------------------------
    guild = interaction.guild
    rol = guild.get_role(ROL_OBJETIVO_ID)

    link_operativo = mensaje_enviado.jump_url

    for member in rol.members:
        try:
            await member.send(
                f"📢 **Nuevo operativo creado**\n\n"
                f"📅 Fecha: {fecha}\n"
                f"🕒 Hora: <t:{ts_operativo}:t>\n\n"
                f"📝 Descripción:\n{descripcion}\n\n"
                f"🔗 Ir al operativo:\n{link_operativo}\n\n"
                f"Marca asistencia cuanto antes.\n"
                f"Si no marcas, se generará sanción automática."
            )
            await asyncio.sleep(0.3)
        except:
            pass  # DMs cerrados
    agregar_operativo(
        mensaje_enviado.id,
        ts_operativo,
        columna_operativo,
)

    await interaction.followup.send(
        "✅ Operativo creado correctamente.",
        ephemeral=True
    )

@bot.tree.command(name="borrarop", description="Borrar operativo")
@app_commands.describe(link="Link del mensaje del operativo")
async def borrarop(interaction: discord.Interaction, link: str):

    member = await interaction.guild.fetch_member(interaction.user.id)

    if not any(rol.id == ROL_ADMIN_ID for rol in member.roles):
        await interaction.followup.send(
            "⛔ No tienes permiso.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    partes = link.split("/")
    mensaje_id = int(partes[-1])
    op = obtener_operativo(mensaje_id)

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

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    from sanciones_manager import (
        obtener_sancion_por_canal,
        actualizar_contador_mensaje
    )

    sancion = obtener_sancion_por_canal(message.channel.id)

    if not sancion:
        await bot.process_commands(message)
        return

    ahora = time.time()
    canal_id = message.channel.id

    # Anti spam (2 segundos mínimo)
    if canal_id in ultimo_update_contador:
        if ahora - ultimo_update_contador[canal_id] < 2:
            await bot.process_commands(message)
            return

    ultimo_update_contador[canal_id] = ahora

    id_sancion = sancion["id_unico"]
    contador_id = sancion.get("contador_mensaje_id")
    fecha_limite = sancion["fecha_limite"]

    # Borrar contador anterior si existe
    if contador_id:
        try:
            viejo = await message.channel.fetch_message(int(contador_id))
            await viejo.delete()
        except:
            pass

    # Enviar nuevo contador
    nuevo = await message.channel.send(
        f"⏳ Fecha límite: <t:{fecha_limite}:F>\n"
        f"Tiempo restante: <t:{fecha_limite}:R>"
    )

    actualizar_contador_mensaje(id_sancion, nuevo.id)

    await bot.process_commands(message)

ultimo_update_contador = {}
bot.run(BOT_TOKEN)