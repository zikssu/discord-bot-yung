import discord
from discord.ext import commands


async def owner_interaction_check(interaction: discord.Interaction) -> bool:
    client = interaction.client
    if (
        isinstance(client, commands.Bot)
        and client.owner_id == interaction.user.id
    ):
        return True

    await interaction.response.send_message(
        "Bot ini hanya dapat digunakan oleh Owner.",
        ephemeral=True,
    )
    return False


class OwnerOnlyView(discord.ui.View):
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await owner_interaction_check(interaction)
