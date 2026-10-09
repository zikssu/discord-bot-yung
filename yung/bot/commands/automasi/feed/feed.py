import discord
from discord import app_commands
from discord.ext import commands
from bot.store import read, write
from bot.commands.automasi.common import BANNER_URL
from datetime import datetime, timezone
from urllib.parse import urlparse
import uuid

CATEGORIES = [
    ("Berita & Informasi", "📰"),
    ("Umum", "🌐"),
]

def posts():
    return read("feed_posts.json", [], feature="feed")

def save_posts(data):
    write("feed_posts.json", data, feature="feed")

def settings():
    return read("feed_settings.json", [], feature="feed")

def save_settings(data):
    write("feed_settings.json", data, feature="feed")

def valid_url(value):
    if not value:
        return True

    parsed = urlparse(value)
    return (
        parsed.scheme in ("http", "https")
        and bool(parsed.netloc)
    )

def split_media_urls(value):
    """Split multiple URLs using the exact separator: space-pipe-space."""
    if not value:
        return []

    return [item.strip() for item in value.split(" | ") if item.strip()]

def get_link_platform(value):
    """Return a friendly platform name for normal web/social links."""
    if not value:
        return "Link"

    hostname = (urlparse(value).hostname or "").lower()
    if hostname.startswith("www."):
        hostname = hostname[4:]

    if hostname == "tiktok.com" or hostname.endswith(".tiktok.com"):
        return "TikTok"
    if hostname in ("x.com", "twitter.com") or hostname.endswith(".x.com") or hostname.endswith(".twitter.com"):
        return "X"
    if hostname == "instagram.com" or hostname.endswith(".instagram.com"):
        return "Instagram"

    return "Link"

def is_image_url(value):
    parsed = urlparse(value) if value else None
    return bool(
        parsed and parsed.path.lower().endswith(
            (".png", ".jpg", ".jpeg", ".gif", ".webp")
        )
    )

def post_embed(data):
    embed = discord.Embed(
        title=data.get("title") or "Postingan",
        description=data.get("caption") or " ",
        color=discord.Color.from_rgb(154, 185, 195),
        timestamp=datetime.fromisoformat(data["created_at"]),
    )
    embed.set_author(
        name=data.get("author_name", "Penghuni home."),
        icon_url=data.get("author_avatar") or discord.Embed.Empty,
    )
    # Metadata dibuat 3 kolom inline:
    # Kategori berada di sebelah kiri Pengirim, lalu Reaksi di sebelah kanan.
    category = data.get("category") or "Umum"
    category_emoji = data.get("emoji") or dict(CATEGORIES).get(category, "🌐")

    embed.add_field(
        name="🏷️ Kategori: ",
        value=f"{category_emoji} {category}",
        inline=True,
    )
    embed.add_field(
        name="👤 Pengirim: ",
        value=f'<@{data["author_id"]}>',
        inline=True,
    )
    # New format supports multiple URLs separated by " | ".
    # Old posts using media_url/media_type remain supported.
    media_urls = data.get("media_urls")
    if not media_urls:
        legacy_url = data.get("media_url")
        media_urls = [legacy_url] if legacy_url else []

    # Discord embeds can display one large image. If there is an image URL,
    # use the first image as the preview and keep every other URL clickable.
    image_url = next((url for url in media_urls if is_image_url(url)), None)
    if image_url:
        embed.set_image(url=image_url)

    # Keep all non-image links in ONE field. Each link gets a platform-specific
    # label (Instagram, TikTok, X, or Link) based on its hostname.
    link_lines = []
    for url in media_urls:
        if url == image_url:
            continue

        platform = get_link_platform(url)
        link_lines.append(f"• [{platform}]({url})")

    if link_lines:
        embed.add_field(
            name="🔗 Link Tautan: ",
            value="\n".join(link_lines),
            inline=False,
        )


    # Count Like/Dislike dipindahkan ke bagian paling bawah embed.
    # Dibuat full-width agar tidak berada satu baris dengan Kategori/Pengirim.
    embed.add_field(
        name="🤔 Reaksi: ",
        value=(
            f'<:kh_like_brawlstars:1547921057393025066>: **{len(data.get("likes", []))}** | '
            f'<:kh_dislike_brawlstars:1547921092465655859>: **{len(data.get("dislikes", []))}**'
        ),
        inline=False,
    )

    embed.set_footer(text="home. • Home Feed")
    return embed

class CategorySelect(discord.ui.Select):
    def __init__(self, cog):
        self.cog = cog
        super().__init__(
            placeholder="Pilih kategori postingan (Berita & Informasi / Umum)...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label=name, emoji=emoji, value=name)
                for name, emoji in CATEGORIES
            ],
            custom_id="feed:category",
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(PostModal(self.cog, self.values[0]))

class CreateView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=300)
        self.add_item(CategorySelect(cog))

class PostModal(discord.ui.Modal):
    title_input = discord.ui.TextInput(
        label="Judul",
        placeholder="Judul postingan",
        max_length=200,
        required=True,
    )
    caption_input = discord.ui.TextInput(
        label="Caption / Informasi",
        style=discord.TextStyle.paragraph,
        placeholder="Ceritakan informasi yang ingin dibagikan...",
        max_length=3500,
        required=True,
    )
    media_input = discord.ui.TextInput(
        label="URL Media / Link (Opsional)",
        placeholder="Link Foto | Video | TikTok | X | Instagram | atau link lainnya...",
        max_length=500,
        required=False,
    )
    image_input = discord.ui.Label(
        text="Upload Image (Opsional)",
        component=discord.ui.FileUpload(
            custom_id="feed_image",
            required=False,
        ),
    )

    def __init__(self, cog, category):
        super().__init__(title="Buat Postingan Feed")
        self.cog = cog
        self.category = category

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message(
                "Gunakan fitur ini di server.", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True, thinking=True)

        cfg = next(
            (item for item in settings()
             if item.get("guild_id") == str(interaction.guild_id)),
            None,
        )
        if not cfg:
            return await interaction.followup.send(
                "Feed belum disiapkan administrator.", ephemeral=True
            )

        channel = interaction.guild.get_channel(int(cfg["channel_id"]))
        if not isinstance(channel, discord.TextChannel):
            return await interaction.followup.send(
                "Channel Feed tidak ditemukan. Minta administrator menjalankan setup ulang.",
                ephemeral=True,
            )

        raw_media = (self.media_input.value or "").strip()
        media_urls = split_media_urls(raw_media)

        invalid_urls = [url for url in media_urls if not valid_url(url)]
        if invalid_urls:
            return await interaction.followup.send(
                "Semua URL harus berupa tautan HTTP/HTTPS yang valid. "
                'Pisahkan beberapa link dengan " | ".',
                ephemeral=True,
            )

        if len(media_urls) > 10:
            return await interaction.followup.send(
                "Maksimal 10 link dapat ditambahkan dalam satu postingan.",
                ephemeral=True,
            )

        # Discord FileUpload returns the selected attachment(s) in .values.
        # FileUpload is nested inside a Label in current discord.py modal APIs.
        file_component = getattr(self.image_input, "component", self.image_input)
        uploaded = getattr(file_component, "values", None) or []
        attachment = uploaded[0] if uploaded else None
        if attachment and not (getattr(attachment, "content_type", "") or "").startswith("image/"):
            return await interaction.followup.send(
                "File yang diunggah harus berupa gambar.", ephemeral=True
            )

        if attachment:
            # Keep an uploaded image together with any URLs entered in the form.
            media_urls.insert(0, attachment.url)

        media_type = "image" if media_urls and is_image_url(media_urls[0]) else (
            "link" if media_urls else None
        )
        final_media_url = media_urls[0] if media_urls else None
        link_platform = (
            get_link_platform(final_media_url)
            if final_media_url and media_type == "link"
            else None
        )

        emoji = dict(CATEGORIES)[self.category]
        data = {
            "id": uuid.uuid4().hex[:10],
            "guild_id": str(interaction.guild_id),
            "channel_id": str(channel.id),
            "message_id": None,
            "thread_id": None,
            "thread_url": None,
            "author_id": str(interaction.user.id),
            "author_name": interaction.user.display_name,
            "author_avatar": interaction.user.display_avatar.url,
            "title": self.title_input.value.strip(),
            "caption": self.caption_input.value.strip(),
            "category": self.category,
            "emoji": emoji,
            # Keep the new multi-link format while retaining legacy fields.
            "media_urls": media_urls,
            "media_url": final_media_url,
            "media_type": media_type,
            "link_platform": link_platform,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "likes": [],
            "dislikes": [],
        }

        try:
            message = await channel.send(
                embed=post_embed(data),
                view=PostView(self.cog, data["id"]),
            )
            data["message_id"] = str(message.id)

            # Create a public thread from the post and expose its direct link in the embed.
            thread = await message.create_thread(
                name="💬 Comment Section",
                auto_archive_duration=1440,
            )
            data["thread_id"] = str(thread.id)
            data["thread_url"] = thread.jump_url
        except discord.Forbidden:
            return await interaction.followup.send(
                "Bot tidak memiliki izin mengirim postingan atau membuat thread. "
                "Periksa izin **Send Messages**, **Create Public Threads**, dan "
                "**Send Messages in Threads** pada channel Feed.",
                ephemeral=True,
            )
        except discord.HTTPException as exc:
            return await interaction.followup.send(
                f"Postingan gagal diproses oleh Discord: `{exc}`",
                ephemeral=True,
            )

        all_posts = posts()
        all_posts.append(data)
        save_posts(all_posts)

        # Send a moderation/audit copy to the configured log channel, if available.
        log_channel_id = cfg.get("log_channel_id")
        log_channel = (
            interaction.guild.get_channel(int(log_channel_id))
            if log_channel_id else None
        )
        if isinstance(log_channel, discord.TextChannel):
            log_embed = discord.Embed(
                title="🧾 Log Home Feed",
                description=f"Postingan baru diterbitkan: [Lihat postingan]({message.jump_url})",
                color=discord.Color.blurple(),
                timestamp=datetime.now(timezone.utc),
            )
            log_embed.add_field(
                name="Pengirim",
                value=f"{interaction.user.mention}\n`{interaction.user.id}`",
                inline=False,
            )
            log_embed.add_field(name="ID Postingan", value=f'`{data["id"]}`', inline=True)
            log_embed.add_field(name="Judul", value=data["title"], inline=True)
            log_embed.add_field(
                name="Kategori",
                value=f"{emoji} {self.category}",
                inline=True,
            )
            try:
                await log_channel.send(embed=log_embed)
            except discord.HTTPException:
                pass

        # Upload berhasil. Jangan tinggalkan ephemeral message setelah proses selesai.
        # Gunakan original interaction response lalu hapus kembali.
        await interaction.edit_original_response(
            content=(
                f"✅ Postingan diterbitkan: {message.jump_url}\n"
                f"💬 Comment Section: {data['thread_url']}"
            )
        )
        await interaction.delete_original_response()

class EditPostModal(discord.ui.Modal):
    def __init__(self, cog, post_id, data):
        super().__init__(title="Edit Postingan Feed")
        self.cog = cog
        self.post_id = post_id
        self.original_data = data

        current_urls = data.get("media_urls")
        if not current_urls:
            legacy_url = data.get("media_url")
            current_urls = [legacy_url] if legacy_url else []

        self.title_input = discord.ui.TextInput(
            label="Judul",
            placeholder="Judul postingan",
            default=data.get("title", ""),
            max_length=200,
            required=True,
        )
        self.caption_input = discord.ui.TextInput(
            label="Caption / Informasi",
            style=discord.TextStyle.paragraph,
            placeholder="Ceritakan informasi yang ingin dibagikan...",
            default=data.get("caption", ""),
            max_length=3500,
            required=True,
        )
        self.media_input = discord.ui.TextInput(
            label="URL Media / Link (Opsional)",
            placeholder="Gunakan \" | \" untuk beberapa link",
            default=" | ".join(current_urls),
            max_length=500,
            required=False,
        )

        self.add_item(self.title_input)
        self.add_item(self.caption_input)
        self.add_item(self.media_input)

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message(
                "Gunakan fitur ini di server.", ephemeral=True
            )

        all_posts = posts()
        data = next((item for item in all_posts if item["id"] == self.post_id), None)
        if not data:
            return await interaction.response.send_message(
                "Postingan tidak ditemukan.", ephemeral=True
            )

        # Only the original author may edit the post.
        is_author = str(interaction.user.id) == str(data.get("author_id"))
        if not is_author:
            return await interaction.response.send_message(
                "Kamu hanya dapat mengedit postingan milikmu sendiri.",
                ephemeral=True,
            )

        raw_media = (self.media_input.value or "").strip()
        media_urls = split_media_urls(raw_media)

        invalid_urls = [url for url in media_urls if not valid_url(url)]
        if invalid_urls:
            return await interaction.response.send_message(
                "Semua URL harus berupa tautan HTTP/HTTPS yang valid. "
                'Pisahkan beberapa link dengan " | ".',
                ephemeral=True,
            )

        if len(media_urls) > 10:
            return await interaction.response.send_message(
                "Maksimal 10 link dapat ditambahkan dalam satu postingan.",
                ephemeral=True,
            )

        # Update the post data without touching likes, dislikes, author,
        # category, creation time, message ID, or comment thread.
        data["title"] = self.title_input.value.strip()
        data["caption"] = self.caption_input.value.strip()
        data["media_urls"] = media_urls
        data["media_url"] = media_urls[0] if media_urls else None
        data["media_type"] = (
            "image" if media_urls and is_image_url(media_urls[0])
            else ("link" if media_urls else None)
        )
        data["link_platform"] = (
            get_link_platform(media_urls[0])
            if media_urls and data["media_type"] == "link"
            else None
        )

        message = interaction.message
        if not message:
            channel = interaction.guild.get_channel(int(data["channel_id"]))
            if isinstance(channel, discord.TextChannel):
                try:
                    message = await channel.fetch_message(int(data["message_id"]))
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    message = None

        if not message:
            return await interaction.response.send_message(
                "Pesan postingan tidak dapat ditemukan di channel Feed.",
                ephemeral=True,
            )

        try:
            await message.edit(
                embed=post_embed(data),
                view=PostView(self.cog, self.post_id),
            )
        except discord.Forbidden:
            return await interaction.response.send_message(
                "Bot tidak memiliki izin untuk mengedit postingan tersebut.",
                ephemeral=True,
            )
        except discord.HTTPException as exc:
            return await interaction.response.send_message(
                f"Postingan gagal diperbarui oleh Discord: `{exc}`",
                ephemeral=True,
            )

        save_posts(all_posts)

        await interaction.response.send_message(
            "✅ Postingan berhasil diperbarui.",
            ephemeral=True,
        )

class PostView(discord.ui.View):
    def __init__(self, cog, post_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.post_id = post_id
        self.add_item(discord.ui.Button(
            emoji="<:kh_like_brawlstars:1547921057393025066>",
            style=discord.ButtonStyle.primary,
            custom_id=f"feed:like:{post_id}",
        ))
        self.add_item(discord.ui.Button(
            emoji="<:kh_dislike_brawlstars:1547921092465655859>",
            style=discord.ButtonStyle.danger,
            custom_id=f"feed:dislike:{post_id}",
        ))
        self.add_item(discord.ui.Button(
            label="Edit",
            emoji="✏️",
            style=discord.ButtonStyle.secondary,
            custom_id=f"feed:edit:{post_id}",
        ))
        self.add_item(discord.ui.Button(
            label="Upload",
            emoji="📝",
            style=discord.ButtonStyle.success,
            custom_id=f"feed:upload:{post_id}",
        ))
        for item in self.children:
            item.callback = self.handle

    async def handle(self, interaction: discord.Interaction):
        action, post_id = interaction.data["custom_id"].split(":")[1:]
        all_posts = posts()
        data = next((item for item in all_posts if item["id"] == post_id), None)
        if not data:
            return await interaction.response.send_message(
                "Postingan tidak ditemukan.", ephemeral=True
            )

        if action == "edit":
            # Only the original author may open the edit form.
            is_author = str(interaction.user.id) == str(data.get("author_id"))
            if not is_author:
                return await interaction.response.send_message(
                    "Kamu hanya dapat mengedit postingan milikmu sendiri.",
                    ephemeral=True,
                )

            return await interaction.response.send_modal(
                EditPostModal(self.cog, post_id, data)
            )

        if action == "upload":
            return await interaction.response.send_message(
                "Pilih kategori postingan:",
                view=CreateView(self.cog),
                ephemeral=True,
            )

        if action not in ("like", "dislike"):
            return await interaction.response.send_message(
                "Aksi tidak dikenali.", ephemeral=True
            )

        user_id = str(interaction.user.id)
        likes = data.setdefault("likes", [])
        dislikes = data.setdefault("dislikes", [])
        own, other = (likes, dislikes) if action == "like" else (dislikes, likes)

        if user_id in own:
            own.remove(user_id)
        else:
            if user_id in other:
                other.remove(user_id)
            own.append(user_id)

        save_posts(all_posts)
        try:
            await interaction.message.edit(
                embed=post_embed(data),
                view=PostView(self.cog, post_id),
            )
        except discord.HTTPException:
            pass

        await interaction.response.send_message(
            f"<:kh_like_brawlstars:1547921057393025066> {len(likes)}  |  <:kh_dislike_brawlstars:1547921092465655859> {len(dislikes)}",
            ephemeral=True,
        )

class Feed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(FeedPanelView(self))
        for post in posts():
            self.bot.add_view(PostView(self, post["id"]))

    @app_commands.command(
        name="setup-feed",
        description="Menyiapkan panel Home Feed home.",
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(
        channel="Channel utama untuk seluruh postingan Feed",
        log_channel="Channel untuk mencatat log postingan Feed",
    )
    async def setup_feed(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        log_channel: discord.TextChannel,
    ):
        if not interaction.guild:
            return await interaction.response.send_message(
                "Gunakan di server.", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True, thinking=True)

        embed = discord.Embed(
            description=(
                "# 📱 Home Feed home.\nBagikan berita, informasi, dokumentasi, kegiatan, dan cerita penghuni di sini.\n\n"
                "**Cara membuat postingan:** tekan tombol **Upload**, pilih "
                'kategori, lalu isi judul, caption, URL media/link, dan/atau unggah gambar '
                'jika diperlukan. Untuk beberapa link, gunakan pemisah "` | `". '
                "URL dan gambar bersifat Opsional."
            ),
            color=discord.Color.from_rgb(154, 185, 195),
        )
        embed.set_image(url=BANNER_URL)

        try:
            panel_message = await channel.send(
                embed=embed,
                view=FeedPanelView(self),
            )
        except discord.Forbidden:
            return await interaction.followup.send(
                "Bot tidak memiliki izin mengirim pesan di channel Feed.",
                ephemeral=True,
            )

        saved = [
            item for item in settings()
            if item.get("guild_id") != str(interaction.guild_id)
        ]
        saved.append({
            "guild_id": str(interaction.guild_id),
            "channel_id": str(channel.id),
            "log_channel_id": str(log_channel.id),
            "panel_message_id": str(panel_message.id),
        })
        save_settings(saved)

        await interaction.followup.send(
            f"✅ Feed disiapkan di {channel.mention}\n"
            f"🧾 Log: {log_channel.mention}\n"
            f"{panel_message.jump_url}",
            ephemeral=True,
        )

    @app_commands.command(
        name="buat-postingan",
        description="Membuat postingan Home Feed home.",
    )
    async def buat_postingan(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Pilih kategori postingan:",
            view=CreateView(self),
            ephemeral=True,
        )

class FeedPanelView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Upload",
        emoji="📝",
        style=discord.ButtonStyle.primary,
        custom_id="feed:open",
    )
    async def open(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Pilih kategori postingan:",
            view=CreateView(self.cog),
            ephemeral=True,
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Feed(bot))
