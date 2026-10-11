import discord
from discord import app_commands
from discord.ext import commands
from bot.store import read, write
from bot.commands.automasi.common import BANNER_URL, DEFAULT
import asyncio

def feedback():
    return read("feedback.json", [], feature="feedback")

def quote_feedback_description(title: str, value: str) -> str:
    quoted_value = "\n".join(f"> {line}" for line in value.splitlines())
    return f"# {title}\n\n{quoted_value}\n\n"

def feedback_author_id(embed: discord.Embed) -> str | None:
    for field in embed.fields:
        if field.name.startswith("👤 Pengirim:"):
            mention = field.value.strip()
            if mention.startswith("<@") and mention.endswith(">"):
                return mention[2:-1].removeprefix("!")
    return None

class FeedbackModal(discord.ui.Modal):
    isi = discord.ui.TextInput(
        label="Ketik Pesanmu dibawah.",
        style=discord.TextStyle.paragraph,
        placeholder="Ketk disini...",
        max_length=4000,
        required=True
    )

    def __init__(self, jenis: str):
        self.jenis = jenis
        super().__init__(title=f"📝 Kirim {jenis}")

    async def on_submit(self, i: discord.Interaction):
        value = self.isi.value.strip()

        if not value:
            return await i.response.send_message(
                "❌ Deskripsi tidak boleh kosong.",
                ephemeral=True
            )

        cfg = next(
            (
                x for x in feedback()
                if x.get("guildId") == str(i.guild_id)
            ),
            None
        )

        if not cfg:
            return await i.response.send_message(
                "❌ Feedback Box belum diatur oleh staf.",
                ephemeral=True
            )

        if not i.guild:
            return await i.response.send_message(
                "❌ Perintah ini hanya dapat digunakan di server.",
                ephemeral=True
            )

        ch = i.guild.get_channel(int(cfg["channelId"]))

        if not isinstance(ch, discord.TextChannel):
            return await i.response.send_message(
                "❌ Channel Kotak Feedback tidak ditemukan.",
                ephemeral=True
            )

        # Tetapkan nama tipe dan emoji secara eksplisit.
        tipe_emoji = {
            "Saran": "💡",
            "Kritik": "🗣️"
        }
        emoji_tipe = tipe_emoji.get(self.jenis, "📝")

        # Isi masukan berada di deskripsi, sebelum field Pengirim dan Tipe.
        e = discord.Embed(
            description=quote_feedback_description(
                f"{emoji_tipe} {self.jenis} Baru!",
                value,
            ),
            color=0xffffff,
            timestamp=discord.utils.utcnow()
        )
        e.add_field(
            name="👤 Pengirim: ",
            value=i.user.mention,
            inline=True
        )
        e.add_field(
            name="🏷️ Tipe: ",
            value=f"{emoji_tipe} {self.jenis}",
            inline=True
        )
        if len(e.description or "") > 4096:
            return await i.response.send_message(
                "❌ Deskripsi terlalu panjang setelah diformat. "
                "Silakan ringkas masukan.",
                ephemeral=True,
            )

        e.set_author(
            name=i.user.name,
            icon_url=i.user.display_avatar.url
        )
        e.set_thumbnail(url=i.user.display_avatar.url)
        e.set_image(url=BANNER_URL)

        # Kiriman masukan menyediakan tombol untuk Saran, Kritik, dan Rating.
        post = await ch.send(
            embed=e,
            view=FeedbackView()
        )

        # Buat kolom komentar
        thread = await post.create_thread(
            name=DEFAULT,
            auto_archive_duration=1440,
            reason="Comment Section Kritik & Saran"
        )

        # Reaksi pada postingan
        for emoji_reaction in ("⬆️", "⬇️"):
            try:
                await post.add_reaction(emoji_reaction)
            except discord.HTTPException as ex:
                print(
                    f"Gagal menambahkan reaksi "
                    f"{emoji_reaction}: {ex}"
                )

        await i.response.send_message(
            f"✅ **{self.jenis} berhasil dikirim!**\n"
            f"📨 Postingan: {post.jump_url}\n"
            f"💬 Comment Section: {thread.mention}",
            ephemeral=True
        )

class RatingModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="⭐ Kirim Rating")
        self.rating = discord.ui.TextInput(
            placeholder="Masukkan angka 1 sampai 5",
            max_length=1,
            required=True,
        )
        self.alasan = discord.ui.TextInput(
            style=discord.TextStyle.paragraph,
            placeholder="Ketik disini...",
            max_length=1000,
            required=True,
        )
        self.add_item(
            discord.ui.Label(
                text="Rating (1-5)",
                component=self.rating,
            )
        )
        self.add_item(
            discord.ui.Label(
                text="Apa Alasan kamu memilih Rating sebesar itu?",
                component=self.alasan,
            )
        )

    async def on_submit(self, i: discord.Interaction):
        rating_value = self.rating.value.strip()
        if rating_value not in {"1", "2", "3", "4", "5"}:
            return await i.response.send_message(
                "❌ Rating harus berupa angka 1 sampai 5.",
                ephemeral=True,
            )

        alasan_value = self.alasan.value.strip()
        if not alasan_value:
            return await i.response.send_message(
                "❌ Alasan rating tidak boleh kosong.",
                ephemeral=True,
            )

        cfg = next(
            (
                x for x in feedback()
                if x.get("guildId") == str(i.guild_id)
            ),
            None,
        )
        if not cfg:
            return await i.response.send_message(
                "❌ Kotak Feedback belum diatur oleh staf.",
                ephemeral=True,
            )

        if not i.guild:
            return await i.response.send_message(
                "❌ Perintah ini hanya dapat digunakan di server.",
                ephemeral=True,
            )

        ch = i.guild.get_channel(int(cfg["channelId"]))
        if not isinstance(ch, discord.TextChannel):
            return await i.response.send_message(
                "❌ Channel Feedback Box tidak ditemukan.",
                ephemeral=True,
            )

        stars = "⭐" * int(rating_value)
        embed = discord.Embed(
            description=quote_feedback_description(
                "⭐ Rating Baru!",
                alasan_value,
            ),
            color=0xffffff,
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="👤 Pengirim: ", value=i.user.mention, inline=True)
        embed.add_field(
            name="⭐ Rating: ",
            value=f"{stars} ({rating_value}/5)",
            inline=True,
        )
        if len(embed.description or "") > 4096:
            return await i.response.send_message(
                "❌ Alasan terlalu panjang setelah diformat. "
                "Silakan ringkas alasan rating.",
                ephemeral=True,
            )
        embed.set_author(name=i.user.name, icon_url=i.user.display_avatar.url)
        embed.set_thumbnail(url=i.user.display_avatar.url)
        embed.set_image(url=BANNER_URL)

        post = await ch.send(embed=embed, view=FeedbackView())
        thread = await post.create_thread(
            name=DEFAULT,
            auto_archive_duration=1440,
            reason="Comment Section Rating",
        )

        for emoji_reaction in ("⬆️", "⬇️"):
            try:
                await post.add_reaction(emoji_reaction)
            except discord.HTTPException as ex:
                print(f"Gagal menambahkan reaksi {emoji_reaction}: {ex}")

        await i.response.send_message(
            "✅ **Rating berhasil dikirim!**\n"
            f"📨 Postingan: {post.jump_url}\n"
            f"💬 Comment Section: {thread.mention}",
            ephemeral=True,
        )

class FeedbackEditModal(discord.ui.Modal):
    def __init__(self, message: discord.Message, embed: discord.Embed):
        self.message = message
        self.original_embed = embed
        self.is_rating = any(
            field.name.startswith("⭐ Rating: ")
            for field in embed.fields
        )
        description = embed.description or ""
        description_parts = description.split("\n\n", maxsplit=1)
        body = description_parts[1].strip() if len(description_parts) == 2 else ""
        if not body:
            legacy_body = next(
                (
                    field.value for field in embed.fields
                    if field.name.strip() in {"", "​"}
                ),
                "",
            )
            body = legacy_body.strip()
        body = "\n".join(
            line[2:] if line.startswith("> ") else line
            for line in body.splitlines()
        )
        super().__init__(
            title="Edit Rating" if self.is_rating else "Edit Masukan"
        )

        self.description_input = discord.ui.TextInput(
            label="Alasan" if self.is_rating else "Deskripsi",
            style=discord.TextStyle.paragraph,
            default=body,
            max_length=3000,
            required=True,
        )

        self.rating_input = None
        if self.is_rating:
            rating_field = next(
                field for field in embed.fields
                if field.name.startswith("⭐ Rating: ")
            )
            rating_value = next(
                (
                    digit for digit in "12345"
                    if f"({digit}/5)" in rating_field.value
                ),
                "",
            )
            self.rating_input = discord.ui.TextInput(
                label="Rating (1-5)",
                default=rating_value,
                max_length=1,
                required=True,
            )
            self.add_item(self.rating_input)
        self.add_item(self.description_input)

    async def on_submit(self, interaction: discord.Interaction):
        if feedback_author_id(self.original_embed) != str(interaction.user.id):
            return await interaction.response.send_message(
                "Kamu hanya dapat mengedit masukan milikmu sendiri.",
                ephemeral=True,
            )

        value = self.description_input.value.strip()
        if not value:
            return await interaction.response.send_message(
                "Deskripsi tidak boleh kosong.",
                ephemeral=True,
            )

        new_embed = self.original_embed.copy()
        title = (self.original_embed.description or "").split("\n", maxsplit=1)[0]
        new_embed.description = quote_feedback_description(
            title.removeprefix("# "),
            value,
        )
        if len(new_embed.description) > 4096:
            return await interaction.response.send_message(
                "Deskripsi terlalu panjang setelah diformat. Silakan ringkas.",
                ephemeral=True,
            )
        if self.is_rating:
            if self.rating_input is None:
                return await interaction.response.send_message(
                    "Kolom rating tidak ditemukan. Silakan coba lagi.",
                    ephemeral=True,
                )
            rating_value = self.rating_input.value.strip()
            if rating_value not in {"1", "2", "3", "4", "5"}:
                return await interaction.response.send_message(
                    "Rating harus berupa angka 1 sampai 5.",
                    ephemeral=True,
                )
            stars = "⭐" * int(rating_value)
            rating_field = next(
                index for index, field in enumerate(new_embed.fields)
                if field.name.startswith("⭐ Rating: ")
            )
            new_embed.set_field_at(
                rating_field,
                name="⭐ Rating: ",
                value=f"{stars} ({rating_value}/5)",
                inline=True,
            )

        try:
            await self.message.edit(embed=new_embed)
        except discord.HTTPException as exc:
            print(f"[Saran] Gagal mengedit masukan: {exc}")
            return await interaction.response.send_message(
                "Masukan gagal diperbarui. Silakan coba lagi.",
                ephemeral=True,
            )

        await interaction.response.send_message(
            "✅ Masukan berhasil diperbarui.",
            ephemeral=True,
        )

class FeedbackView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Kirim Saran",
        emoji="💡",
        style=discord.ButtonStyle.primary,
        custom_id="saran:open:saran"
    )
    async def open_saran(
        self,
        i: discord.Interaction,
        button: discord.ui.Button
    ):
        await i.response.send_modal(
            FeedbackModal("Saran")
        )

    @discord.ui.button(
        label="Kirim Kritik",
        emoji="🗣️",
        style=discord.ButtonStyle.secondary,
        custom_id="saran:open:kritik"
    )
    async def open_kritik(
        self,
        i: discord.Interaction,
        button: discord.ui.Button
    ):
        await i.response.send_modal(
            FeedbackModal("Kritik")
        )

    @discord.ui.button(
        label="Kirim Rating",
        emoji="⭐",
        style=discord.ButtonStyle.success,
        custom_id="saran:open:rating",
    )
    async def open_rating(
        self,
        i: discord.Interaction,
        button: discord.ui.Button,
    ):
        await i.response.send_modal(RatingModal())

    @discord.ui.button(
        label="Edit",
        emoji="✏️",
        style=discord.ButtonStyle.secondary,
        custom_id="saran:feedback:edit",
        row=1,
    )
    async def edit_feedback(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        message = interaction.message
        embed = message.embeds[0] if message and message.embeds else None
        if not message or not embed or not feedback_author_id(embed):
            return await interaction.response.send_message(
                "Informasi pemilik masukan tidak ditemukan.",
                ephemeral=True,
            )
        if feedback_author_id(embed) != str(interaction.user.id):
            return await interaction.response.send_message(
                "Kamu hanya dapat mengedit masukan milikmu sendiri.",
                ephemeral=True,
            )
        await interaction.response.send_modal(FeedbackEditModal(message, embed))

class FeedbackPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Kirim Saran",
        emoji="💡",
        style=discord.ButtonStyle.primary,
        custom_id="saran:panel:open:saran",
    )
    async def open_saran(
        self,
        i: discord.Interaction,
        button: discord.ui.Button,
    ):
        await i.response.send_modal(FeedbackModal("Saran"))

    @discord.ui.button(
        label="Kirim Kritik",
        emoji="🗣️",
        style=discord.ButtonStyle.secondary,
        custom_id="saran:panel:open:kritik",
    )
    async def open_kritik(
        self,
        i: discord.Interaction,
        button: discord.ui.Button,
    ):
        await i.response.send_modal(FeedbackModal("Kritik"))

    @discord.ui.button(
        label="Kirim Rating",
        emoji="⭐",
        style=discord.ButtonStyle.success,
        custom_id="saran:panel:open:rating",
    )
    async def open_rating(
        self,
        i: discord.Interaction,
        button: discord.ui.Button,
    ):
        await i.response.send_modal(RatingModal())

class FeedbackCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._feedback_setup_lock = asyncio.Lock()

    @app_commands.command(
        name="setup-feedback",
        description="Mengatur channel Feedback Box"
    )
    @app_commands.default_permissions(
        manage_channels=True
    )
    @app_commands.describe(
        channel="Channel untuk Feedback Box"
    )
    async def setup_feedback(
        self,
        i: discord.Interaction,
        channel: discord.TextChannel
    ):
        await i.response.defer(ephemeral=True)

        e = discord.Embed(
            description=(
                "# 📮 Feedback Box\n"
                "Punya ide, kritik, atau saran untuk "
                "home.? Sampaikan melalui "
                "formulir di bawah ini. Setiap masukan "
                "membantu penghuni membangun komunitas bersama.\n\n"
                "**Pilih tombol sesuai masukan kamu:**\n"
                "> 💡 **Kirim Saran** - ide dan usulan.\n"
                "> 🗣️ **Kirim Kritik** - evaluasi dan hal yang perlu diperbaiki.\n"
                "> ⭐ **Kirim Rating** - beri nilai 1–5 beserta alasannya."
            ),
            color=0xffffff
        )

        e.set_image(url=BANNER_URL)

        async with self._feedback_setup_lock:
            configs = feedback()
            previous_config = next(
                (
                    item for item in configs
                    if item.get("guildId") == str(i.guild_id)
                ),
                None,
            )
            posted = None
            matching_panels = []
            should_find_legacy_panel = bool(
                previous_config
                and previous_config.get("channelId") == str(channel.id)
            )

            if should_find_legacy_panel:
                panel_message_id = previous_config.get("panelMessageId")
                if panel_message_id:
                    try:
                        posted = await channel.fetch_message(
                            int(panel_message_id)
                        )
                    except discord.NotFound:
                        posted = None
                    except discord.HTTPException as exc:
                        print(f"[Feedback] Gagal mengambil panel sebelumnya: {exc}")
                        return await i.followup.send(
                            "❌ Panel sebelumnya tidak dapat diperiksa. "
                            "Tidak ada panel baru yang dikirim.",
                            ephemeral=True,
                        )

            if should_find_legacy_panel and not posted:
                try:
                    async for message in channel.history(limit=100):
                        if (
                            message.author.id == self.bot.user.id
                            and any(
                                embed.description
                                and embed.description.startswith(
                                    "# 📮 Feedback Box"
                                )
                                for embed in message.embeds
                            )
                        ):
                            matching_panels.append(message)
                except discord.HTTPException as exc:
                    print(f"[Feedback] Gagal memeriksa panel sebelumnya: {exc}")
                    return await i.followup.send(
                        "❌ Riwayat channel tidak dapat diperiksa. "
                        "Tidak ada panel baru yang dikirim.",
                        ephemeral=True,
                    )

                if matching_panels:
                    posted = matching_panels[0]

            try:
                if posted:
                    await posted.edit(embed=e, view=FeedbackPanelView())
                else:
                    posted = await channel.send(embed=e, view=FeedbackPanelView())
            except discord.HTTPException as exc:
                print(f"[Feedback] Gagal menyimpan panel: {exc}")
                return await i.followup.send(
                    "❌ Panel Feedback Box gagal dibuat atau diperbarui.",
                    ephemeral=True,
                )

            cleanup_failed = False
            for duplicate in matching_panels:
                if duplicate.id == posted.id:
                    continue
                try:
                    await duplicate.delete(
                        reason="Membersihkan duplikat panel Feedback Box"
                    )
                except discord.HTTPException as exc:
                    cleanup_failed = True
                    print(
                        f"[Feedback] Gagal menghapus panel duplikat "
                        f"{duplicate.id}: {exc}"
                    )

            data = [
                item for item in configs
                if item.get("guildId") != str(i.guild_id)
            ]
            data.append({
                "guildId": str(i.guild_id),
                "channelId": str(channel.id),
                "panelMessageId": str(posted.id),
            })
            write("feedback.json", data, feature="feedback")

        result = (
            "✅ **Feedback Box berhasil diperbarui!**"
            if previous_config
            else "✅ **Feedback Box berhasil disiapkan!**"
        )
        if cleanup_failed:
            result += (
                "\n⚠️ Sebagian panel duplikat tidak dapat dihapus. "
                "Periksa izin bot **Manage Messages** pada channel tersebut."
            )
        await i.followup.send(
            f"{result}\n**Channel:** {channel.mention}\n"
            f"**Panel:** {posted.jump_url}",
            ephemeral=True,
        )

async def setup(bot: commands.Bot):
    cog = FeedbackCog(bot)
    bot.add_view(FeedbackView())
    bot.add_view(FeedbackPanelView())
    await bot.add_cog(cog)
