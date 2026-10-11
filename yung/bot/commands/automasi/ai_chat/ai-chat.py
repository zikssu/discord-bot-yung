import asyncio
import logging
import os
from collections.abc import AsyncIterator

import discord
import httpx
from discord import app_commands
from discord.ext import commands
from google import genai
from google.genai import errors

from bot.store import read, write

MODEL_NAME = "gemini-3.8-flash"
GEMINI_REQUEST_TIMEOUT_SECONDS = 30
MAX_OUTPUT_TOKENS = 400
DISCORD_MESSAGE_LIMIT = 1900
_STREAM_DONE = object()
logger = logging.getLogger(__name__)


def ai_chat_settings():
    return read("ai_chat_settings.json", [], feature="ai_chat")


async def stream_gemini_text(
    client: genai.Client,
    prompt: str,
) -> AsyncIterator[str]:
    loop = asyncio.get_running_loop()
    chunks: asyncio.Queue[str | Exception | object] = asyncio.Queue()

    def publish(value: str | Exception | object) -> None:
        loop.call_soon_threadsafe(chunks.put_nowait, value)

    def request_stream() -> None:
        try:
            stream = client.interactions.create(
                model=MODEL_NAME,
                input=prompt,
                stream=True,
                timeout=GEMINI_REQUEST_TIMEOUT_SECONDS,
                system_instruction=(
                    "Jawab menggunakan bahasa yang sama dengan pengguna. "
                    "Berikan jawaban yang jelas dan ringkas."
                ),
                generation_config={"max_output_tokens": MAX_OUTPUT_TOKENS},
            )
            for event in stream:
                if event.event_type == "error":
                    error_message = event.error.message or "Unknown Gemini error"
                    raise RuntimeError(error_message)
                if (
                    event.event_type == "step.delta"
                    and event.delta.type == "text"
                    and event.delta.text
                ):
                    publish(event.delta.text)
        except Exception as error:
            publish(error)
        finally:
            publish(_STREAM_DONE)

    worker = asyncio.create_task(asyncio.to_thread(request_stream))
    try:
        while True:
            chunk = await chunks.get()
            if chunk is _STREAM_DONE:
                break
            if isinstance(chunk, Exception):
                raise chunk
            if isinstance(chunk, str):
                yield chunk
        await worker
    finally:
        if not worker.done():
            await worker


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
        if self.client is None:
            return await interaction.response.send_message(
                "AI Chat belum siap karena GEMINI_API_KEY tidak tersedia. "
                "Periksa konfigurasi bot lalu restart bot.",
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
            logger.error("AI Chat tidak dapat merespons: API key tidak tersedia.")
            return await message.reply(
                "AI Chat belum siap. Minta administrator memeriksa "
                "konfigurasi Gemini.",
                mention_author=False,
            )

        logger.info(
            "AI Chat mulai memproses pesan (guild_id=%s, channel_id=%s).",
            message.guild.id,
            message.channel.id,
        )
        response_parts: list[str] = []

        try:
            async with message.channel.typing():
                async for text in stream_gemini_text(
                    self.client,
                    message.content,
                ):
                    response_parts.append(text)

            output = "".join(response_parts)
            if not output.strip():
                raise ValueError("Gemini menyelesaikan request tanpa teks.")

            chunks = [
                output[index : index + DISCORD_MESSAGE_LIMIT]
                for index in range(0, len(output), DISCORD_MESSAGE_LIMIT)
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

            logger.info(
                "AI Chat selesai merespons (guild_id=%s, channel_id=%s).",
                message.guild.id,
                message.channel.id,
            )
        except (httpx.TimeoutException, TimeoutError):
            logger.exception(
                "AI Chat timeout setelah %s detik (guild_id=%s, channel_id=%s).",
                GEMINI_REQUEST_TIMEOUT_SECONDS,
                message.guild.id,
                message.channel.id,
            )
            await message.reply(
                f"⌛ Gemini belum selesai dalam "
                f"{GEMINI_REQUEST_TIMEOUT_SECONDS} detik. "
                "Coba kirim pesan yang lebih singkat.",
                mention_author=False,
            )
        except errors.APIError as error:
            logger.exception(
                "Gemini API error (status=%s, guild_id=%s, channel_id=%s).",
                error.code,
                message.guild.id,
                message.channel.id,
            )
            await message.reply(
                f"⚠️ Gemini menolak atau gagal memproses permintaan "
                f"(status {error.code}). Periksa log bot untuk detail.",
                mention_author=False,
            )
        except (httpx.HTTPError, RuntimeError, ValueError):
            logger.exception(
                "AI Chat gagal memproses streaming Gemini "
                "(guild_id=%s, channel_id=%s).",
                message.guild.id,
                message.channel.id,
            )
            await message.reply(
                "⚠️ AI Chat gagal memproses pesan. "
                "Periksa log bot untuk detail.",
                mention_author=False,
            )
        except discord.HTTPException:
            logger.exception(
                "Gagal mengirim jawaban/error AI Chat "
                "(guild_id=%s, channel_id=%s).",
                message.guild.id,
                message.channel.id,
            )


async def setup(bot):
    await bot.add_cog(AiChatCog(bot))
