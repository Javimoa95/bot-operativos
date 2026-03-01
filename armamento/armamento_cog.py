import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import pytz
from discord.app_commands import Choice
from .armamento_parser import parsear_mensaje
from .armamento_manager import (
    insertar_log,
    obtener_logs_usuario,
    obtener_logs_desde
)

from .armamento_exporter import (
    generar_json_semana,
    mover_a_historial,
    obtener_semana_actual,
    obtener_ultima_semana_exportada,
    actualizar_semana_exportada,
    CANAL_EXPORTES_ARMAMENTO_ID
)

CANAL_ARMAMENTO_LOGS_ID = 1342237928533000282

# ---------------------------------------------------------

def inicio_semana_timestamp():
    tz = pytz.timezone("Europe/Madrid")
    ahora = datetime.now(tz)
    inicio = ahora - timedelta(days=ahora.weekday())
    inicio = inicio.replace(hour=0, minute=0, second=0, microsecond=0)
    return int(inicio.timestamp())

def parsear_fecha(fecha_str):
    tz = pytz.timezone("Europe/Madrid")

    try:
        dia, mes = map(int, fecha_str.split("/"))
    except:
        return inicio_semana_timestamp()

    anio = datetime.now(tz).year
    fecha = datetime(anio, mes, dia, 0, 0)
    fecha = tz.localize(fecha)
    return int(fecha.timestamp())# ---------------------------------------------------------

class Armamento(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.revisar_semana.start()

    # ---------------- LISTENER ----------------

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.channel.id != CANAL_ARMAMENTO_LOGS_ID:
            return

        if message.webhook_id is None:
            return

        data = parsear_mensaje(message)
        if not data:
            return

        insertar_log(data)

    # ---------------- RECUPERACIÓN AL INICIAR ----------------

    async def recuperar_ultimos_logs(self):
        print("🔁 Recuperando últimos 50 logs...")

        try:
            canal = await self.bot.fetch_channel(CANAL_ARMAMENTO_LOGS_ID)
        except Exception as e:
            print("Error obteniendo canal:", e)
            return

        async for message in canal.history(limit=50):
            print("MENSAJE:", message.content)

            if message.webhook_id is None:
                continue

            data = parsear_mensaje(message)

            if not data:
                print("❌ NO PARSEADO")
                continue

            print("✅ PARSEADO:", data)
            insertar_log(data)
        print("✅ Recuperación completada")

    # ---------------- /ARMAMENTO ----------------

    @app_commands.command(name="armamento", description="Ver estadísticas de un usuario")
    @app_commands.describe(
        usuario="Usuario a consultar",
        fecha="Fecha desde (DD/MM) opcional",
        categoria="Filtrar por categoría"
    )
    @app_commands.choices(categoria=[
        Choice(name="🔫 Armas", value="armas"),
        Choice(name="💣 Munición", value="municion"),
        Choice(name="🛡 Equipamiento", value="equipamiento"),
        Choice(name="🍔 Comida", value="comida"),
        Choice(name="🌿 Drogas", value="drogas"),
        Choice(name="📦 Otros", value="otros")
    ])
    async def armamento(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        fecha: str = None,
        categoria: Choice[str] = None
    ):    
        await interaction.response.defer()

        timestamp_inicio = parsear_fecha(fecha) if fecha else inicio_semana_timestamp()

        logs = obtener_logs_usuario(usuario.display_name, timestamp_inicio)

        if not logs:
            await interaction.followup.send("No hay datos para ese usuario.")
            return

        stats = {}

        for row in logs:

            if categoria is not None and row["categoria"] != categoria.value:
                continue
            codigo = row["objeto_codigo"]
            nombre = row["objeto_nombre"]
            tipo = row["tipo"]
            cantidad = row["cantidad"]

            if codigo not in stats:
                stats[codigo] = {
                    "nombre": nombre,
                    "metido": 0,
                    "sacado": 0
                }

            stats[codigo][tipo] += cantidad
        nombre_categoria = "Todas"

        if categoria:
            nombre_categoria = categoria.name  # Ej: "🔫 Armas"
        
        color_categoria = discord.Color.blue()
        if categoria:
            if categoria.value == "armas":
                color_categoria = discord.Color.red()
            elif categoria.value == "municion":
                color_categoria = discord.Color.orange()
            elif categoria.value == "equipamiento":
                color_categoria = discord.Color.gold()
            elif categoria.value == "comida":
                color_categoria = discord.Color.green()
            elif categoria.value == "drogas":
                color_categoria = discord.Color.purple()
                
        embed = discord.Embed(
            title="📊 Informe de Armamento",
            color=color_categoria
        )
        texto = ""
        balance_total = 0

        for data in stats.values():

            balance = data["metido"] - data["sacado"]
            balance_total += balance

            if data["metido"] == 0 and data["sacado"] == 0:
                continue

            # Emoji según arma
            nombre_lower = data["nombre"].lower()

            if "9mm" in nombre_lower:
                emoji = "🔫"
            elif "revolver" in nombre_lower:
                emoji = "🔫"
            elif "sns" in nombre_lower:
                emoji = "💥"
            elif "mk2" in nombre_lower:
                emoji = "🚀"
            elif "escopeta" in nombre_lower:
                emoji = "💣"
            elif "knife" in nombre_lower or "cuchillo" in nombre_lower:
                emoji = "🔪"
            else:
                emoji = "🔹"

            linea = f"{emoji} **{data['nombre']}**\n"

            if data["metido"] > 0:
                linea += f"➕ Metido: ✅ `{data['metido']}`  "

            if data["sacado"] > 0:
                linea += f"➖ Sacado: ❌ `{data['sacado']}`"

            linea += "\n\n"

            texto += linea

        emoji_balance = "🟢" if balance_total >= 0 else "🔴"
        texto += f"\n⚖ **Balance Neto:** {emoji_balance} `{balance_total}`"

        embed = discord.Embed(
            title="📊 Informe de Armamento",
            color=color_categoria
        )

        embed.description = (
            f"👤 **Usuario:** {usuario.mention}\n"
            f"📂 **Categoría:** {nombre_categoria}\n\n"
            f"{texto}"
        )

        embed.set_footer(text="The Demons • Sistema de Armamento")
        embed.set_thumbnail(url=usuario.display_avatar.url)

        await interaction.followup.send(embed=embed)
    # ---------------- /RECUENTO ----------------

    @app_commands.command(name="recuento", description="Balance general de armas")
    @app_commands.describe(
        fecha="Fecha desde (DD/MM) opcional"
    )
    async def recuento(
        self,
        interaction: discord.Interaction,
        fecha: str = None
    ):
        await interaction.response.defer()

        timestamp_inicio = parsear_fecha(fecha) if fecha else inicio_semana_timestamp()

        logs = obtener_logs_desde(timestamp_inicio)

        if not logs:
            await interaction.followup.send("⚠ No hay datos.")
            return

        usuarios = {}

        for row in logs:

            # Detectar armas directamente por código
            if not row["objeto_codigo"].startswith("WEAPON_"):
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

        embed = discord.Embed(
            title="📈 Recuento Global de Armas",
            color=discord.Color.red()
        )

        if not usuarios:
            embed.description = "⚠ No hay movimientos de armas esta semana."
        else:
            texto = ""
            for data in usuarios.values():
                balance = data["metido"] - data["sacado"]
                emoji = "🟢" if balance >= 0 else "🔴"
                texto += f"👤 **{data['username']}** → ⚖ {emoji} `{balance}`\n"

            embed.description = texto

        await interaction.followup.send(embed=embed)
    # ---------------- EXPORTACIÓN SEMANAL ----------------

    @tasks.loop(minutes=1)
    async def revisar_semana(self):

        semana_actual = obtener_semana_actual()
        ultima = obtener_ultima_semana_exportada()

        # Si nunca se ha guardado semana, solo guardar y salir
        if ultima is None:
            actualizar_semana_exportada(semana_actual)
            return

        if ultima == semana_actual:
            return
        resultado = generar_json_semana()

        if not resultado:
            actualizar_semana_exportada(semana_actual)
            return

        nombre_archivo, semana = resultado
        canal = self.bot.get_channel(CANAL_EXPORTES_ARMAMENTO_ID)

        if canal:
            await canal.send(
                content=f"📦 Logs semana {semana}",
                file=discord.File(nombre_archivo)
            )

        mover_a_historial(semana)
        actualizar_semana_exportada(semana)

    @revisar_semana.before_loop
    async def before_revisar_semana(self):
        await self.bot.wait_until_ready()

# ---------------------------------------------------------

async def setup(bot):
    cog = Armamento(bot)
    await bot.add_cog(cog)
    await cog.recuperar_ultimos_logs()