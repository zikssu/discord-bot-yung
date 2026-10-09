import discord
from discord import app_commands
from discord.ext import commands

from bot.commands.utilitas.common import EMBED_COLOR, BANNER_URL


class InfoServerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="infoserver",
        description="Melihat informasi server Discord.",
    )
    async def infoserver(self, interaction: discord.Interaction):
        """Menampilkan informasi server tempat command digunakan."""
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "Command ini hanya bisa digunakan di server.",
                ephemeral=True,
            )
            return

        owner = guild.owner
        if owner is None:
            owner = await guild.fetch_member(guild.owner_id)

        embed = discord.Embed(
            title=f"🏡 {guild.name}",
            color=EMBED_COLOR,
            description="Informasi server Discord.",
        )
        embed.add_field(name="ID Server", value=str(guild.id), inline=True)
        embed.add_field(name="Pemilik", value=str(owner), inline=True)
        embed.add_field(
            name="Jumlah Anggota",
            value=str(guild.member_count or 0),
            inline=True,
        )
        embed.add_field(
            name="Dibuat",
            value=f"<t:{int(guild.created_at.timestamp())}:D>",
            inline=True,
        )
        if BANNER_URL:
            embed.set_image(url=BANNER_URL)

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(InfoServerCog(bot))
