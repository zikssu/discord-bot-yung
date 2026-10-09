import discord
from discord import app_commands
from discord.ext import commands

from bot.commands.utilitas.common import EMBED_COLOR


class InfoUserCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="infouser",
        description="Melihat informasi pengguna Discord.",
    )
    @app_commands.describe(
        pengguna="Pengguna yang ingin diperiksa",
    )
    async def infouser(
        self,
        interaction: discord.Interaction,
        pengguna: discord.User | None = None,
    ):
        """Menampilkan informasi pengguna yang dipilih atau pengguna sendiri."""
        user = pengguna or interaction.user
        member = (
            interaction.guild.get_member(user.id)
            if interaction.guild
            else None
        )

        embed = discord.Embed(
            title="👤 Informasi Pengguna",
            color=EMBED_COLOR,
            description=f"Profil Discord untuk {user.mention}.",
        )
        embed.add_field(name="Username", value=str(user), inline=True)
        embed.add_field(name="ID Pengguna", value=str(user.id), inline=True)
        embed.add_field(
            name="Akun Bot",
            value="Ya" if user.bot else "Tidak",
            inline=True,
        )
        embed.add_field(
            name="Akun Dibuat",
            value=f"<t:{int(user.created_at.timestamp())}:D>",
            inline=True,
        )
        if member and member.joined_at:
            embed.add_field(
                name="📅 Bergabung ke server",
                value=f"<t:{int(member.joined_at.timestamp())}:D>",
                inline=False,
            )

        embed.set_thumbnail(url=user.display_avatar.url)

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(InfoUserCog(bot))
