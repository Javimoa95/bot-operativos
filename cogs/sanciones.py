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
        fecha="Fecha límite DD/MM"
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
        member = await interaction.guild.fetch_member(interaction.user.id)
        if not any(r.id == ROL_SANCIONADOR_ID for r in member.roles):
            await interaction.response.send_message(
                "⛔ No tienes permisos para usar este comando.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        # ---- PARSEAR FECHA SOLO DD/MM ----
        tz = pytz.timezone("Europe/Madrid")
        try:
            dia, mes = map(int, fecha.split("/"))

            anio = datetime.now(tz).year

            # Hora automática 00:00
            fecha_dt = datetime(anio, mes, dia, 0, 0)
            fecha_dt = tz.localize(fecha_dt)

            timestamp = int(fecha_dt.timestamp())
        except:
            await interaction.followup.send(
                "Formato fecha incorrecto. Usa DD/MM",
                ephemeral=True
            )
            return

        pistolas = nivel

        mensaje = (
            f"**SANCION NIVEL {nivel} ARMAMENTISTICA :**\n\n"
            f"Tienes 1 aviso y debes de entregar: **{pistolas} pipas**\n\n"
            f"**Fecha limite:** <t:{timestamp}:d>\n\n"
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
        from sanciones_manager import crear_sancion, crear_canal_sancion, actualizar_canal_sancion

        id_sancion = crear_sancion(
            usuario.id,
            nivel,
            motivo,
            timestamp
        )

        mensaje_publico = await canal.send(mensaje)

        link_mensaje = mensaje_publico.jump_url

        canal_id = await crear_canal_sancion(
            self.bot,
            interaction.guild,
            usuario,
            id_sancion,
            timestamp,
            link_mensaje
        )

        actualizar_canal_sancion(
            id_sancion,
            canal_id,
            mensaje_publico.id
        )
        await interaction.followup.send(
            "✅ Sanción enviada correctamente.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Sanciones(bot))
