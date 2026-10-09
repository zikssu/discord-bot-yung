import discord
from discord import app_commands
from discord.ext import commands

from bot.commands.utilitas.common import EMBED_COLOR


class PingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="ping",
        description="Memeriksa latensi Homi",
    )
    async def ping(self, interaction: discord.Interaction):
        """Menampilkan latensi WebSocket bot."""
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description="Status koneksi bot.",
            color=EMBED_COLOR,
        )
        embed.add_field(
            name="Latensi WebSocket",
            value=f"`{latency} ms`",
            inline=False,
        )
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(PingCog(bot))
