import asyncio
import logging
import os

import discord
import httpx
from discord import app_commands
from discord.ext import commands
from google import genai
from google.genai import errors

from bot.store import read, write

MODEL_NAME = "gemini-3.8-flash"
GEMINI_REQUEST_TIMEOUT_SECONDS = 10
logger = logging.getLogger(__name__)


def ai_chat_settings():
    return read("ai_chat_settings.json", [], feature="ai_chat")


class AiChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key) if api_key else None

    def cog_unload(self):
        if self.client is not None:
            self.client.close()

    @app_commands.command(
        name="setup-ai-chat",
        description="Mengatur channel untuk percakapan AI otomatis.",
    )
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.describe(channel="Channel khusus untuk percakapan dengan AI")
    async def setup_ai_chat(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ):
        if not interaction.guild:
            return await interaction.response.send_message(
                "Command ini hanya dapat digunakan di dalam server.",
                ephemeral=True,
            )
        if not os.getenv("GEMINI_API_KEY"):
            return await interaction.response.send_message(
                "GEMINI_API_KEY belum diatur. Minta administrator untuk "
                "menambahkan API key Gemini ke file .env.",
                ephemeral=True,
            )

        settings = ai_chat_settings()
        guild_id = str(interaction.guild.id)
        config = next(
            (item for item in settings if item.get("guildId") == guild_id),
            None,
        )
        if config is None:
            settings.append(
                {"guildId": guild_id, "channelId": str(channel.id)}
            )
        else:
            config["channelId"] = str(channel.id)
        write("ai_chat_settings.json", settings, feature="ai_chat")

        await interaction.response.send_message(
            f"✅ AI Chat aktif di {channel.mention}. "
            "Pesan yang dikirim di sana akan dijawab otomatis.",
            ephemeral=True,
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if (
            message.author.bot
            or not message.guild
            or not message.content.strip()
        ):
            return

        config = next(
            (
                item
                for item in ai_chat_settings()
                if item.get("guildId") == str(message.guild.id)
                and item.get("channelId") == str(message.channel.id)
            ),
            None,
        )
        if config is None:
            return

        if self.client is None:
            print("AI Chat gagal: GEMINI_API_KEY belum diatur.")
            return await message.reply(
                "AI Chat belum tersedia karena API key Gemini belum diatur.",
                mention_author=False,
            )

        try:
            async with message.channel.typing():
                interaction = await asyncio.to_thread(
                    self.client.interactions.create,
                    model=MODEL_NAME,
                    input=message.content,
                    timeout=GEMINI_REQUEST_TIMEOUT_SECONDS,
                )
            output = interaction.output_text
            if not output or not output.strip():
                raise ValueError("Gemini mengembalikan jawaban kosong.")
        except (httpx.TimeoutException, TimeoutError):
            logger.exception(
                "AI Chat timeout setelah %s detik.",
                GEMINI_REQUEST_TIMEOUT_SECONDS,
            )
            return await message.reply(
                "Maaf, Gemini tidak merespons dalam 60 detik. "
                "Coba kirim pesan lagi nanti.",
                mention_author=False,
            )
        except (errors.APIError, httpx.HTTPError, ValueError):
            logger.exception("AI Chat gagal memproses pesan melalui Gemini.")
            return await message.reply(
                "Maaf, AI Chat sedang mengalami kendala. Coba lagi nanti.",
                mention_author=False,
            )

        chunks = [
            output[index : index + 2000]
            for index in range(0, len(output), 2000)
        ]
        await message.reply(
            chunks[0],
            mention_author=False,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        for chunk in chunks[1:]:
            await message.channel.send(
                chunk,
                allowed_mentions=discord.AllowedMentions.none(),
            )


async def setup(bot):
    await bot.add_cog(AiChatCog(bot))
