from discord.ext import commands
from discord import app_commands
import discord
from datetime import datetime
import pytz

ROL_SANCIONADOR_ID = 1346520439433728060
CANAL_SANCIONES_ID = 1220866157649727489

class Sanciones(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="sancion", description="Crear sanción")
    @app_commands.describe(
        nivel="Nivel de sanción (1,2,3...)",
        usuario="Usuario sancionado",
        motivo="Motivo de la sanción",
        fecha="Fecha límite DD/MM HH:MM"
    )
    async def sancion(
        self,
        interaction: discord.Interaction,
        nivel: int,
        usuario: discord.Member,
        motivo: str,
        fecha: str
    ):

        # ---- PERMISOS ----
        member = interaction.guild.get_member(interaction.user.id)
        if not any(r.id == ROL_SANCIONADOR_ID for r in member.roles):
            await interaction.response.send_message(
                "⛔ No tienes permisos para usar este comando.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        # ---- PARSEAR FECHA ----
        tz = pytz.timezone("Europe/Madrid")
        try:
            dia, resto = fecha.split("/")
            mes, hora = resto.split(" ")
            h, m = hora.split(":")

            ahora = datetime.now(tz)
            anio = ahora.year

            fecha_dt = datetime(anio, int(mes), int(dia), int(h), int(m))
            fecha_dt = tz.localize(fecha_dt)

            timestamp = int(fecha_dt.timestamp())
        except:
            await interaction.followup.send(
                "Formato fecha incorrecto. Usa DD/MM HH:MM",
                ephemeral=True
            )
            return

        pistolas = nivel

        mensaje = (
            f"**SANCION NIVEL {nivel} ARMAMENTISTICA :**\n\n"
            f"Tienes 1 aviso y debes de entregar: **{pistolas} pipas**\n\n"
            f"**Fecha limite:** <t:{timestamp}:s>\n\n"
            f"**Usuario sancionado:** {usuario.mention}\n\n"
            f"**Motivo:** {motivo}\n\n"
            f"Cualquier duda o fallo abre ticket.\n"
            f"Si cumples la sancion abre ticket con las pruebas y tagueame."
        )

        # ---- CANAL FIJO ----
        canal = self.bot.get_channel(CANAL_SANCIONES_ID)
        if canal is None:
            await interaction.followup.send(
                "❌ Canal de sanciones no encontrado.",
                ephemeral=True
            )
            return

        await canal.send(mensaje)

        await interaction.followup.send(
            "✅ Sanción enviada correctamente.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Sanciones(bot))
