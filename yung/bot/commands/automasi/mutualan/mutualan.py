import discord
from discord import app_commands
from discord.ext import commands
from bot.store import read, write
from bot.commands.automasi.common import BANNER_URL
from urllib.parse import urlparse
import uuid

SOCIAL_FIELDS = [
    ("instagram", "Instagram", "<:kh_instagram:1546673046746562602>", "https://instagram.com/username"),
    ("tiktok", "TikTok", "<:kh_tiktok:1546673122525188196>", "https://tiktok.com/@username"),
    ("facebook", "Facebook", "<:kh_facebook:1554520636716490832>", "https://facebook.com/username"),
    ("x", "X", "<:kh_x:1546673178003116062>", "https://x.com/username"),
    ("whatsapp", "Saluran WhatsApp", "<:kh_whatsapp:1546673322018738226>", "https://whatsapp.com/channel/..."),
]

def mutual_profiles():
    return read("mutual_medsos.json", [], feature="mutualan")

def save_mutual_profiles(data):
    write("mutual_medsos.json", data, feature="mutualan")

def mutual_settings():
    return read("mutual_medsos_settings.json", [], feature="mutualan")

def save_mutual_settings(data):
    write("mutual_medsos_settings.json", data, feature="mutualan")

def valid_social_url(value):
    if not value:
        return True
    parsed = urlparse(value)
    return (
        parsed.scheme in ("http", "https")
        and bool(parsed.netloc)
        and "." in parsed.netloc
    )

def mutual_embed(profile, user=None):
    embed = discord.Embed(
        description=(
            "# 📲 Mutualan Media Sosial\n"
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

    # Banner server ditampilkan di bagian bawah profil mutualan.
    if BANNER_URL:
        embed.set_image(url=BANNER_URL)
    return embed

class MutualUploadFirstModal(discord.ui.Modal):
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
        for key, label, emoji, placeholder in SOCIAL_FIELDS:
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
        await self.cog.save_mutual_profile(interaction, values)

class MutualPanelView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Upload",
        emoji="📤",
        style=discord.ButtonStyle.primary,
        custom_id="mutual:upload",
    )
    async def upload(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            MutualUploadFirstModal(self.cog, "upload")
        )

class MutualProfileView(discord.ui.View):
    def __init__(self, cog, profile):
        super().__init__(timeout=None)
        self.cog = cog
        self.profile_id = profile["id"]

        # Link tombol hanya dibuat untuk platform yang memiliki URL.
        for key, label, emoji, _ in SOCIAL_FIELDS:
            url = (profile.get(key) or "").strip()
            if url:
                self.add_item(discord.ui.Button(
                    label=label,
                    emoji=emoji,
                    style=discord.ButtonStyle.link,
                    url=url,
                ))

        edit_button = discord.ui.Button(
            label="Edit",
            emoji="✏️",
            style=discord.ButtonStyle.secondary,
            custom_id=f"mutual:profile-edit:{self.profile_id}",
        )
        edit_button.callback = self.edit_profile
        self.add_item(edit_button)

        delete_button = discord.ui.Button(
            label="Hapus",
            emoji="🗑️",
            style=discord.ButtonStyle.danger,
            custom_id=f"mutual:profile-delete:{self.profile_id}",
        )
        delete_button.callback = self.delete_profile
        self.add_item(delete_button)

        upload_button = discord.ui.Button(
            label="Upload",
            emoji="📤",
            style=discord.ButtonStyle.primary,
            custom_id=f"mutual:profile-upload:{self.profile_id}",
        )
        upload_button.callback = self.upload_profile
        self.add_item(upload_button)

    def get_profile(self):
        return next(
            (
                item for item in mutual_profiles()
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
            MutualUploadFirstModal(self.cog, "edit", profile)
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
            MutualUploadFirstModal(self.cog, "upload", profile)
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
            item for item in mutual_profiles()
            if item.get("id") != self.profile_id
        ]
        save_mutual_profiles(data)

        # Hapus thread komentar jika masih ada.
        if interaction.guild and profile.get("thread_id"):
            try:
                thread = interaction.guild.get_thread(int(profile["thread_id"]))
                if thread is None and interaction.message:
                    channel = interaction.message.channel
                    if isinstance(channel, discord.TextChannel):
                        thread = channel.get_thread(int(profile["thread_id"]))
                if thread:
                    await thread.delete(reason="Profil Mutualan Media Sosial dihapus")
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
            "✅ Profil Mutualan Media Sosial berhasil dihapus.",
            ephemeral=True,
        )

class MutualanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="setup-mutual-medsos",
        description="Membuat panel Mutualan Media Sosial"
    )
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.describe(channel="Channel untuk panel Mutualan Media Sosial")
    async def setup_mutual_medsos(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ):
        panel = discord.Embed(
            description=(
                "# 📲 Mutualan Media Sosial\n"
                "Yuk, saling terhubung dengan penghuni home.!\n\n"
                "Tekan **Upload** untuk mengisi tautan media sosial kamu. "
                "Setelah profil dibuat, kamu dapat menggunakan tombol **Edit**, **Hapus**, atau **Upload** pada profilmu."
            ),
            color=discord.Color.from_rgb(154, 185, 195),
        )
        panel.set_image(url=BANNER_URL)

        message = await channel.send(embed=panel, view=MutualPanelView(self))
        configs = [
            item for item in mutual_settings()
            if item.get("guild_id") != str(interaction.guild_id)
        ]
        configs.append({
            "guild_id": str(interaction.guild_id),
            "channel_id": str(channel.id),
            "panel_message_id": str(message.id),
        })
        save_mutual_settings(configs)

        await interaction.response.send_message(
            f"✅ Panel Mutualan berhasil dibuat di {channel.mention}.\n"
            f"[Lihat panel]({message.jump_url})",
            ephemeral=True,
        )

    async def save_mutual_profile(self, interaction, values):
        if not interaction.guild:
            return await interaction.response.send_message(
                "Fitur ini hanya dapat digunakan di server.", ephemeral=True
            )

        cfg = next(
            (item for item in mutual_settings()
             if item.get("guild_id") == str(interaction.guild_id)),
            None,
        )
        if not cfg:
            return await interaction.response.send_message(
                "Panel Mutualan belum disiapkan administrator.", ephemeral=True
            )

        channel = interaction.guild.get_channel(int(cfg["channel_id"]))
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                "Channel Mutualan tidak ditemukan. Minta admin menjalankan setup ulang.",
                ephemeral=True,
            )

        data = mutual_profiles()
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
                    embed=mutual_embed(profile),
                    view=MutualProfileView(self, profile),
                )
                profile["message_id"] = str(message.id)
                thread = await message.create_thread(
                    name="💬 Comment Section",
                    auto_archive_duration=1440,
                    reason="Kolom komentar Mutualan Media Sosial",
                )
                profile["thread_id"] = str(thread.id)
            else:
                profile_message = await channel.fetch_message(int(profile["message_id"]))
                await profile_message.edit(
                    embed=mutual_embed(profile),
                    view=MutualProfileView(self, profile),
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
        save_mutual_profiles(data)
        await interaction.response.send_message(
            "✅ Profil Mutualan kamu berhasil "
            + ("diunggah." if is_new else "diperbarui.")
            + "\n💬 Comment Section: 💬 Comment Section",
            ephemeral=True,
        )

async def setup(bot: commands.Bot):
    cog = MutualanCog(bot)
    bot.add_view(MutualPanelView(cog))
    for profile in mutual_profiles():
        if profile.get("message_id"):
            bot.add_view(
                MutualProfileView(cog, profile),
                message_id=int(profile["message_id"]),
            )
    await bot.add_cog(cog)
