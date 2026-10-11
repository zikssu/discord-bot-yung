import discord
from discord import app_commands
from discord.ext import commands
from bot.store import read, write
from bot.commands.automasi.common import BANNER_URL
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageOps
from urllib.parse import urlparse
import uuid

SOCIAL_FIELDS = [
    ("instagram", "Instagram", "Instagram.png", "https://instagram.com/username"),
    ("tiktok", "TikTok", "tiktok.png", "https://tiktok.com/@username"),
    ("facebook", "Facebook", "facebook.png", "https://facebook.com/username"),
    ("x", "X", "x.png", "https://x.com/username"),
    ("whatsapp", "Saluran WhatsApp", "whatsapp.png", "https://whatsapp.com/channel/..."),
]

MOOTS_ASSETS_DIR = Path(__file__).resolve().parents[4] / "assets" / "moots"


def moots_emoji_image(filename: str) -> bytes:
    with Image.open(MOOTS_ASSETS_DIR / filename) as source:
        image = ImageOps.contain(
            source.convert("RGBA"),
            (128, 128),
            method=Image.Resampling.LANCZOS,
        )
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


async def ensure_moots_emojis(guild: discord.Guild) -> dict[str, str]:
    existing = {emoji.name: emoji for emoji in guild.emojis}
    emoji_ids = {}

    for key, _, filename, _ in SOCIAL_FIELDS:
        name = f"moots_{key}"
        emoji = existing.get(name)
        if emoji is None:
            emoji = await guild.create_custom_emoji(
                name=name,
                image=moots_emoji_image(filename),
                reason="Menyiapkan ikon tombol Moots",
            )
            existing[name] = emoji
        emoji_ids[key] = str(emoji.id)

    return emoji_ids


def moots_profiles():
    return read("moots.json", [], feature="moots")

def save_moots_profiles(data):
    write("moots.json", data, feature="moots")

def moots_settings():
    return read("moots_settings.json", [], feature="moots")

def save_moots_settings(data):
    write("moots_settings.json", data, feature="moots")

def valid_social_url(value):
    if not value:
        return True
    parsed = urlparse(value)
    return (
        parsed.scheme in ("http", "https")
        and bool(parsed.netloc)
        and "." in parsed.netloc
    )

def moots_embed(profile, user=None):
    embed = discord.Embed(
        description=(
            "# 📲 Moots\n"
            "Berikut media sosial "
            f"<@{profile['user_id']}> yang bisa kamu kunjungi."
        ),
        color=discord.Color.from_rgb(154, 185, 195),
    )
    # Nama user tidak ditampilkan lagi karena user sudah disebut
    # langsung melalui User Mention pada deskripsi. Avatar tetap
    # ditampilkan di sisi kanan embed melalui thumbnail Discord.
    avatar_url = profile.get("avatar_url") or None
    if avatar_url:
        embed.set_thumbnail(url=avatar_url)

    return embed

class MootsUploadFirstModal(discord.ui.Modal):
    def __init__(self, cog, mode, existing=None):
        super().__init__(
            title="Upload Media Sosial" if mode == "upload" else "Edit Media Sosial"
        )
        self.cog = cog
        self.mode = mode
        self.existing = existing or {}
        self.inputs = {}

        # Discord Modal maksimal memiliki 5 komponen TextInput.
        # Lima platform ini karena Threads sudah dihapus.
        for key, label, _, placeholder in SOCIAL_FIELDS:
            field = discord.ui.TextInput(
                label=label,
                placeholder=placeholder,
                default=self.existing.get(key, "") or None,
                required=False,
                max_length=300,
            )
            self.inputs[key] = field
            self.add_item(field)

    async def on_submit(self, interaction: discord.Interaction):
        values = {
            key: (field.value or "").strip()
            for key, field in self.inputs.items()
        }

        invalid = [
            label
            for key, label, _, _ in SOCIAL_FIELDS
            if values.get(key) and not valid_social_url(values[key])
        ]
        if invalid:
            return await interaction.response.send_message(
                "❌ URL tidak valid untuk: "
                + ", ".join(invalid)
                + ". Gunakan tautan lengkap yang diawali http:// atau https://.",
                ephemeral=True,
            )

        # Langsung simpan. Tidak ada langkah kedua / modal Threads.
        await self.cog.save_moots_profile(interaction, values)

class MootsPanelView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Upload",
        emoji="📤",
        style=discord.ButtonStyle.primary,
        custom_id="moots:upload",
    )
    async def upload(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            MootsUploadFirstModal(self.cog, "upload")
        )

class MootsProfileView(discord.ui.View):
    def __init__(self, cog, profile, emoji_ids=None):
        super().__init__(timeout=None)
        self.cog = cog
        self.profile_id = profile["id"]
        emoji_ids = emoji_ids or {}

        # Link tombol hanya dibuat untuk platform yang memiliki URL.
        for key, label, _, _ in SOCIAL_FIELDS:
            url = (profile.get(key) or "").strip()
            if url:
                emoji_id = emoji_ids.get(key)
                emoji = (
                    discord.PartialEmoji(name=f"moots_{key}", id=int(emoji_id))
                    if emoji_id
                    else None
                )
                self.add_item(
                    discord.ui.Button(
                        label=label,
                        emoji=emoji,
                        style=discord.ButtonStyle.link,
                        url=url,
                        row=0,
                    )
                )

        edit_button = discord.ui.Button(
            label="Edit",
            emoji="✏️",
            style=discord.ButtonStyle.secondary,
            custom_id=f"moots:profile-edit:{self.profile_id}",
            row=1,
        )
        edit_button.callback = self.edit_profile
        self.add_item(edit_button)

        delete_button = discord.ui.Button(
            label="Hapus",
            emoji="🗑️",
            style=discord.ButtonStyle.danger,
            custom_id=f"moots:profile-delete:{self.profile_id}",
            row=1,
        )
        delete_button.callback = self.delete_profile
        self.add_item(delete_button)

        upload_button = discord.ui.Button(
            label="Upload",
            emoji="📤",
            style=discord.ButtonStyle.primary,
            custom_id=f"moots:profile-upload:{self.profile_id}",
            row=1,
        )
        upload_button.callback = self.upload_profile
        self.add_item(upload_button)

    def get_profile(self):
        return next(
            (
                item for item in moots_profiles()
                if item.get("id") == self.profile_id
            ),
            None,
        )

    async def edit_profile(self, interaction: discord.Interaction):
        profile = self.get_profile()
        if not profile:
            return await interaction.response.send_message(
                "Profil tidak ditemukan.", ephemeral=True
            )

        if profile.get("user_id") != str(interaction.user.id):
            return await interaction.response.send_message(
                "Kamu hanya dapat Mengedit Profil Milikmu sendiri.",
                ephemeral=True,
            )

        await interaction.response.send_modal(
            MootsUploadFirstModal(self.cog, "edit", profile)
        )

    async def upload_profile(self, interaction: discord.Interaction):
        profile = self.get_profile()
        if not profile:
            return await interaction.response.send_message(
                "Profil tidak ditemukan.", ephemeral=True
            )

        if profile.get("user_id") != str(interaction.user.id):
            return await interaction.response.send_message(
                "Kamu hanya dapat Mengunggah Ulang Profil Milikmu sendiri.",
                ephemeral=True,
            )

        # Upload dari profil membuka satu form yang sama dan langsung menyimpan.
        await interaction.response.send_modal(
            MootsUploadFirstModal(self.cog, "upload", profile)
        )

    async def delete_profile(self, interaction: discord.Interaction):
        profile = self.get_profile()
        if not profile:
            return await interaction.response.send_message(
                "Profil tidak ditemukan.", ephemeral=True
            )

        if profile.get("user_id") != str(interaction.user.id):
            return await interaction.response.send_message(
                "Kamu hanya dapat Menghapus Profil Milikmu sendiri.",
                ephemeral=True,
            )

        # Hapus data profil dari penyimpanan terlebih dahulu.
        data = [
            item for item in moots_profiles()
            if item.get("id") != self.profile_id
        ]
        save_moots_profiles(data)

        # Hapus thread komentar jika masih ada.
        if interaction.guild and profile.get("thread_id"):
            try:
                thread = interaction.guild.get_thread(int(profile["thread_id"]))
                if thread is None and interaction.message:
                    channel = interaction.message.channel
                    if isinstance(channel, discord.TextChannel):
                        thread = channel.get_thread(int(profile["thread_id"]))
                if thread:
                    await thread.delete(reason="Profil Moots dihapus")
            except (discord.NotFound, discord.Forbidden, discord.HTTPException, ValueError):
                pass

        # Hapus pesan profil.
        try:
            if interaction.message:
                await interaction.message.delete()
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return await interaction.response.send_message(
                "✅ Data profil sudah dihapus, tetapi pesan profil tidak dapat dihapus oleh bot.",
                ephemeral=True,
            )

        await interaction.response.send_message(
            "✅ Profil Moots berhasil dihapus.",
            ephemeral=True,
        )

class MootsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="setup-moots",
        description="Membuat panel Moots"
    )
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.describe(channel="Channel untuk panel Moots")
    async def setup_moots(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ):
        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message(
                "Perintah ini hanya dapat digunakan di server.",
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            emoji_ids = await ensure_moots_emojis(guild)
        except discord.Forbidden as exc:
            print(f"[Moots] Bot tidak dapat membuat emoji server: {exc}")
            return await interaction.followup.send(
                "❌ Bot tidak memiliki izin **Manage Emojis and Stickers** "
                "atau server kehabisan slot emoji. Beri izin/slot yang cukup, "
                "lalu jalankan `/setup-moots` kembali.",
                ephemeral=True,
            )
        except discord.HTTPException as exc:
            print(f"[Moots] Gagal membuat emoji tombol: {exc}")
            if exc.code == 30008:
                return await interaction.followup.send(
                    "❌ Slot emoji server sudah penuh. Hapus atau tambah slot "
                    "emoji, lalu jalankan `/setup-moots` kembali.",
                    ephemeral=True,
                )
            return await interaction.followup.send(
                f"❌ Emoji tombol Moots gagal dibuat: `{exc}`",
                ephemeral=True,
            )
        except OSError as exc:
            print(f"[Moots] Gagal membaca aset emoji: {exc}")
            return await interaction.followup.send(
                "❌ Aset logo Moots tidak dapat dibaca. Periksa file di "
                "`yung/assets/moots/`.",
                ephemeral=True,
            )

        panel = discord.Embed(
            description=(
                "# 📲 Moots\n"
                "Yuk, saling terhubung dengan penghuni home.!\n\n"
                "Tekan **Upload** untuk mengisi tautan media sosial kamu. "
                "Setelah profil dibuat, kamu dapat menggunakan tombol **Edit**, **Hapus**, atau **Upload** pada profilmu."
            ),
            color=discord.Color.from_rgb(154, 185, 195),
        )
        panel.set_image(url=BANNER_URL)

        try:
            message = await channel.send(embed=panel, view=MootsPanelView(self))
        except discord.Forbidden as exc:
            print(f"[Moots] Bot tidak dapat mengirim panel: {exc}")
            return await interaction.followup.send(
                "❌ Bot tidak memiliki izin mengirim panel ke channel tersebut.",
                ephemeral=True,
            )
        except discord.HTTPException as exc:
            print(f"[Moots] Gagal mengirim panel: {exc}")
            return await interaction.followup.send(
                f"❌ Panel Moots gagal dikirim: `{exc}`",
                ephemeral=True,
            )

        configs = [
            item for item in moots_settings()
            if item.get("guild_id") != str(interaction.guild_id)
        ]
        configs.append({
            "guild_id": str(interaction.guild_id),
            "channel_id": str(channel.id),
            "panel_message_id": str(message.id),
            "emoji_ids": emoji_ids,
        })
        save_moots_settings(configs)

        await interaction.followup.send(
            f"✅ Panel Moots berhasil dibuat di {channel.mention}.\n"
            f"[Lihat panel]({message.jump_url})",
            ephemeral=True,
        )

    async def save_moots_profile(self, interaction, values):
        if not interaction.guild:
            return await interaction.response.send_message(
                "Fitur ini hanya dapat digunakan di server.", ephemeral=True
            )

        cfg = next(
            (item for item in moots_settings()
             if item.get("guild_id") == str(interaction.guild_id)),
            None,
        )
        if not cfg:
            return await interaction.response.send_message(
                "Panel Moots belum disiapkan oleh tim Administrator.", ephemeral=True
            )

        channel = interaction.guild.get_channel(int(cfg["channel_id"]))
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                "Channel Moots tidak ditemukan. Minta admin menjalankan setup ulang.",
                ephemeral=True,
            )

        data = moots_profiles()
        profile = next(
            (item for item in data
             if item.get("guild_id") == str(interaction.guild_id)
             and item.get("user_id") == str(interaction.user.id)),
            None,
        )
        is_new = profile is None
        if is_new:
            profile = {
                "id": uuid.uuid4().hex[:12],
                "guild_id": str(interaction.guild_id),
                "user_id": str(interaction.user.id),
                "message_id": None,
                "thread_id": None,
            }

        profile.update(values)
        profile.pop("threads", None)
        profile["display_name"] = interaction.user.display_name
        profile["avatar_url"] = interaction.user.display_avatar.url

        try:
            if is_new:
                message = await channel.send(
                    embed=moots_embed(profile),
                    view=MootsProfileView(self, profile, cfg.get("emoji_ids")),
                )
                profile["message_id"] = str(message.id)
                thread = await message.create_thread(
                    name="💬 Comment Section",
                    auto_archive_duration=1440,
                    reason="Kolom komentar Moots",
                )
                profile["thread_id"] = str(thread.id)
            else:
                profile_message = await channel.fetch_message(int(profile["message_id"]))
                await profile_message.edit(
                    embed=moots_embed(profile),
                    view=MootsProfileView(self, profile, cfg.get("emoji_ids")),
                    attachments=[],
                )
        except discord.Forbidden:
            return await interaction.response.send_message(
                "Bot tidak memiliki izin mengirim/mengedit pesan atau membuat thread. "
                "Periksa Send Messages, Embed Links, Create Public Threads, dan "
                "Send Messages in Threads.",
                ephemeral=True,
            )
        except discord.HTTPException as exc:
            return await interaction.response.send_message(
                f"Profil gagal diproses oleh Discord: `{exc}`",
                ephemeral=True,
            )

        if is_new:
            data.append(profile)
        save_moots_profiles(data)
        await interaction.response.send_message(
            "✅ Profil Moots kamu berhasil "
            + ("diunggah." if is_new else "diperbarui.")
            + "\n💬 Comment Section: 💬 Comment Section",
            ephemeral=True,
        )

async def setup(bot: commands.Bot):
    cog = MootsCog(bot)
    bot.add_view(MootsPanelView(cog))
    emoji_ids_by_guild = {
        str(item.get("guild_id")): item.get("emoji_ids", {})
        for item in moots_settings()
    }
    for profile in moots_profiles():
        if profile.get("message_id"):
            bot.add_view(
                MootsProfileView(
                    cog,
                    profile,
                    emoji_ids_by_guild.get(str(profile.get("guild_id"))),
                ),
                message_id=int(profile["message_id"]),
            )
    await bot.add_cog(cog)
