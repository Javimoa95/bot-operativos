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

        # ---- PARSEAR FECHA ----
        tz = pytz.timezone("Europe/Madrid")
        try:
            dia, mes = map(int, fecha.split("/"))
            anio = datetime.now(tz).year
            fecha_dt = datetime(anio, mes, dia, 0, 0)
            fecha_dt = tz.localize(fecha_dt)
            timestamp = int(fecha_dt.timestamp())
        except:
            await interaction.followup.send(
                "Formato fecha incorrecto. Usa DD/MM",
                ephemeral=True
            )
            return

        from sanciones_manager import (
            crear_sancion,
            crear_canal_sancion,
            actualizar_canal_sancion
        )

        # ---- CREAR SANCION EN DB ----
        id_sancion = crear_sancion(
            usuario.id,
            nivel,
            motivo,
            timestamp
        )

        # ---- CANAL PUBLICO ----
        canal_publico = interaction.guild.get_channel(CANAL_SANCIONES_ID)

        if not canal_publico:
            await interaction.followup.send(
                "❌ Canal de sanciones no encontrado.",
                ephemeral=True
            )
            return

        # ---- MENSAJE PUBLICO ----
        mensaje_publico = await canal_publico.send(
            f"**SANCION NIVEL {nivel} ARMAMENTISTICA :**\n\n"
            f"**ID Sanción:** `{id_sancion}`\n\n"
            f"Tienes 1 aviso y debes de entregar: **{nivel} pipas**\n\n"
            f"**Fecha limite:** <t:{timestamp}:d>\n\n"
            f"**Usuario sancionado:** {usuario.mention}\n\n"
            f"**Motivo:** {motivo}\n\n"
            f"Cualquier duda o fallo abre ticket.\n"
            f"Si cumples la sancion abre ticket con las pruebas y tagueame."
        )

        link_mensaje = mensaje_publico.jump_url

        # ---- CREAR CANAL PRIVADO ----
        canal_id, mensaje_privado_id, contador_id = await crear_canal_sancion(
            self.bot,
            interaction.guild,
            usuario,
            id_sancion,
            timestamp,
            link_mensaje
        )

        # ---- GUARDAR TODO EN DB ----
        actualizar_canal_sancion(
            id_sancion,
            canal_id,
            mensaje_privado_id,
            mensaje_publico.id,
            contador_id
        )
        await interaction.followup.send(
            "✅ Sanción enviada correctamente.",
            ephemeral=True
        )
    @app_commands.command(name="borrarsancion", description="Borrar sanción")
    @app_commands.describe(id_sancion="ID único de la sanción")
    async def borrar_sancion_cmd(
        self,
        interaction: discord.Interaction,
        id_sancion: str
    ):

        member = await interaction.guild.fetch_member(interaction.user.id)

        if not any(r.id == ROL_SANCIONADOR_ID for r in member.roles):
            await interaction.response.send_message(
                "⛔ No tienes permisos.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        from sanciones_manager import obtener_sancion, borrar_sancion

        sancion = obtener_sancion(id_sancion)

        if not sancion:
            await interaction.followup.send(
                "❌ Sanción no encontrada.",
                ephemeral=True
            )
            return

        canal_id = sancion["canal_id"]
        mensaje_publico_id = sancion["mensaje_sancion_id"]

        # ---- BORRAR CANAL PRIVADO ----
        if canal_id:
            try:
                canal = await self.bot.fetch_channel(canal_id)
            except:
                canal = None
            if canal:
                await canal.delete()

        # ---- BORRAR MENSAJE PUBLICO ----
        if mensaje_publico_id:
            try:
                canal_sanciones = await self.bot.fetch_channel(CANAL_SANCIONES_ID)
            except:
                canal_sanciones = None
            if canal_sanciones:
                try:
                    mensaje = await canal_sanciones.fetch_message(mensaje_publico_id)
                    await mensaje.delete()
                except:
                    pass

        # ---- BORRAR DE DB ----
        borrar_sancion(id_sancion)

        await interaction.followup.send(
            f"🗑 Sanción `{id_sancion}` eliminada correctamente.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Sanciones(bot))
