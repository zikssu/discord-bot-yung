import discord
from discord import app_commands
from discord.ext import commands
from bot.store import read, write
from bot.commands.automasi.common import BANNER_URL
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageOps
from urllib.parse import urlparse
import uuid

REACTION_ASSETS = {
    "like": "like_brawl_stars.png",
    "dislike": "dislike_brawl_stars.png",
}
FEED_ASSETS_DIR = Path(__file__).resolve().parents[4] / "assets" / "feed"

CATEGORIES = [
    ("Berita & Informasi", "📰"),
    ("Umum", "🌐"),
    ("Hiburan", "🎭"),
    ("Pendidikan", "📚"),
    ("Gaya Hidup (Lifestyle)", "🏖️"),
    ("Edukasi & Tutorial", "🛠️"),
]

def posts():
    return read("feed_posts.json", [], feature="feed")

def save_posts(data):
    write("feed_posts.json", data, feature="feed")

def settings():
    return read("feed_settings.json", [], feature="feed")

def save_settings(data):
    write("feed_settings.json", data, feature="feed")

def reaction_emoji_ids(guild_id):
    config = next(
        (item for item in settings() if item.get("guild_id") == str(guild_id)),
        None,
    )
    return config.get("reaction_emoji_ids", {}) if config else {}

def reaction_emoji(guild_id, action):
    emoji_id = reaction_emoji_ids(guild_id).get(action)
    if emoji_id:
        return f"<:feed_{action}:{emoji_id}>"
    return "👍🏻" if action == "like" else "👎🏻"

def reaction_emoji_image(filename):
    with Image.open(FEED_ASSETS_DIR / filename) as source:
        image = ImageOps.contain(
            source.convert("RGBA"),
            (128, 128),
            method=Image.Resampling.LANCZOS,
        )
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()

async def ensure_feed_reaction_emojis(guild):
    existing = {emoji.name: emoji for emoji in guild.emojis}
    emoji_ids = {}

    for action, filename in REACTION_ASSETS.items():
        name = f"feed_{action}"
        emoji = existing.get(name)
        if emoji is None:
            emoji = await guild.create_custom_emoji(
                name=name,
                image=reaction_emoji_image(filename),
                reason="Menyiapkan ikon Like/Dislike Home Feed",
            )
            existing[name] = emoji
        emoji_ids[action] = str(emoji.id)

    return emoji_ids

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
    like_emoji = reaction_emoji(data.get("guild_id"), "like")
    dislike_emoji = reaction_emoji(data.get("guild_id"), "dislike")
    caption = data.get("caption") or " "
    quoted_caption = "\n".join(f"> {line}" for line in caption.splitlines())
    embed = discord.Embed(
        title=data.get("title") or "Postingan",
        description=f"{quoted_caption}\n\n",
        color=discord.Color.from_rgb(154, 185, 195),
        timestamp=datetime.fromisoformat(data["created_at"]),
    )
    embed.set_author(
        name=data.get("author_name", "Penghuni home."),
    )
    author_avatar = data.get("author_avatar")
    if author_avatar:
        embed.set_thumbnail(url=author_avatar)
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
            f'{like_emoji}: **{len(data.get("likes", []))}** | '
            f'{dislike_emoji}: **{len(data.get("dislikes", []))}**'
        ),
        inline=False,
    )

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
                view=PostView(
                    self.cog,
                    data["id"],
                    reaction_emoji_ids(data["guild_id"]),
                ),
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
                title="🧾 Log Feed",
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
                view=PostView(
                    self.cog,
                    self.post_id,
                    reaction_emoji_ids(data.get("guild_id")),
                ),
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
    def __init__(self, cog, post_id, emoji_ids=None):
        super().__init__(timeout=None)
        self.cog = cog
        self.post_id = post_id
        emoji_ids = emoji_ids or {}
        like_emoji_id = emoji_ids.get("like")
        dislike_emoji_id = emoji_ids.get("dislike")
        self.add_item(discord.ui.Button(
            emoji=(
                discord.PartialEmoji(name="feed_like", id=int(like_emoji_id))
                if like_emoji_id
                else "👍🏻"
            ),
            style=discord.ButtonStyle.primary,
            custom_id=f"feed:like:{post_id}",
            row=0,
        ))
        self.add_item(discord.ui.Button(
            emoji=(
                discord.PartialEmoji(name="feed_dislike", id=int(dislike_emoji_id))
                if dislike_emoji_id
                else "👎🏻"
            ),
            style=discord.ButtonStyle.danger,
            custom_id=f"feed:dislike:{post_id}",
            row=0,
        ))
        self.add_item(discord.ui.Button(
            label="Edit",
            emoji="✏️",
            style=discord.ButtonStyle.secondary,
            custom_id=f"feed:edit:{post_id}",
            row=1,
        ))
        self.add_item(discord.ui.Button(
            label="Upload",
            emoji="📝",
            style=discord.ButtonStyle.success,
            custom_id=f"feed:upload:{post_id}",
            row=1,
        ))
        self.add_item(discord.ui.Button(
            label="Hapus",
            emoji="🗑️",
            style=discord.ButtonStyle.danger,
            custom_id=f"feed:delete:{post_id}",
            row=1,
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

        if action == "delete":
            if str(interaction.user.id) != str(data.get("author_id")):
                return await interaction.response.send_message(
                    "Kamu hanya dapat menghapus postingan milikmu sendiri.",
                    ephemeral=True,
                )

            message = interaction.message
            if message is None:
                return await interaction.response.send_message(
                    "Pesan postingan tidak ditemukan, jadi tidak ada yang dihapus.",
                    ephemeral=True,
                )

            thread_cleanup_failed = False
            thread_id = data.get("thread_id")
            if interaction.guild and thread_id:
                thread = interaction.guild.get_thread(int(thread_id))
                if thread is None and isinstance(message.channel, discord.TextChannel):
                    thread = message.channel.get_thread(int(thread_id))
                if thread is not None:
                    try:
                        await thread.delete(reason="Postingan Feed dihapus pemiliknya")
                    except discord.NotFound:
                        pass
                    except (discord.Forbidden, discord.HTTPException) as exc:
                        thread_cleanup_failed = True
                        print(
                            f"[Feed] Gagal menghapus thread {thread_id} "
                            f"untuk postingan {post_id}: {exc}"
                        )

            try:
                await message.delete()
            except discord.NotFound:
                pass
            except discord.Forbidden as exc:
                print(f"[Feed] Tidak dapat menghapus pesan {message.id}: {exc}")
                return await interaction.response.send_message(
                    "Bot tidak memiliki izin untuk menghapus pesan postingan.",
                    ephemeral=True,
                )
            except discord.HTTPException as exc:
                print(f"[Feed] Gagal menghapus pesan {message.id}: {exc}")
                return await interaction.response.send_message(
                    f"Postingan gagal dihapus oleh Discord: `{exc}`",
                    ephemeral=True,
                )

            all_posts.remove(data)
            save_posts(all_posts)
            result = "✅ Postingan Feed berhasil dihapus."
            if thread_cleanup_failed:
                result += (
                    "\n⚠️ Postingan terhapus, tetapi thread komentarnya tidak "
                    "dapat dihapus. Periksa izin bot pada thread."
                )
            return await interaction.response.send_message(
                result,
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
                view=PostView(
                    self.cog,
                    post_id,
                    reaction_emoji_ids(data.get("guild_id")),
                ),
            )
        except discord.HTTPException:
            pass

        await interaction.response.send_message(
            f"{reaction_emoji(data.get('guild_id'), 'like')} {len(likes)}  |  "
            f"{reaction_emoji(data.get('guild_id'), 'dislike')} {len(dislikes)}",
            ephemeral=True,
        )

class Feed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(FeedPanelView(self))
        for post in posts():
            self.bot.add_view(
                PostView(
                    self,
                    post["id"],
                    reaction_emoji_ids(post.get("guild_id")),
                )
            )

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
        guild = interaction.guild

        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            reaction_emoji_ids_saved = await ensure_feed_reaction_emojis(guild)
        except discord.Forbidden as exc:
            print(f"[Feed] Bot tidak dapat membuat emoji server: {exc}")
            return await interaction.followup.send(
                "❌ Bot tidak memiliki izin **Manage Emojis and Stickers** "
                "atau server kehabisan slot emoji. Beri izin/slot yang cukup, "
                "lalu jalankan `/setup-feed` kembali.",
                ephemeral=True,
            )
        except discord.HTTPException as exc:
            print(f"[Feed] Gagal membuat emoji Like/Dislike: {exc}")
            if exc.code == 30008:
                return await interaction.followup.send(
                    "❌ Slot emoji server sudah penuh. Hapus atau tambah slot "
                    "emoji, lalu jalankan `/setup-feed` kembali.",
                    ephemeral=True,
                )
            return await interaction.followup.send(
                f"❌ Ikon Like/Dislike gagal dibuat: `{exc}`",
                ephemeral=True,
            )
        except OSError as exc:
            print(f"[Feed] Gagal membaca aset ikon reaksi: {exc}")
            return await interaction.followup.send(
                "❌ Aset ikon Like/Dislike tidak dapat dibaca. Periksa file di "
                "`yung/assets/feed/`.",
                ephemeral=True,
            )

        embed = discord.Embed(
            description=(
                "# 📱 Feed Server\nBagikan berita, informasi, dokumentasi, kegiatan, dan cerita penghuni di sini.\n\n"
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
            "reaction_emoji_ids": reaction_emoji_ids_saved,
        })
        save_settings(saved)

        updated_posts = 0
        failed_posts = []
        for post in posts():
            if (
                str(post.get("guild_id")) != str(guild.id)
                or not post.get("message_id")
                or not post.get("channel_id")
            ):
                continue

            post_channel = guild.get_channel(int(post["channel_id"]))
            if not isinstance(post_channel, discord.TextChannel):
                failed_posts.append(post.get("id", post["message_id"]))
                continue

            try:
                post_message = await post_channel.fetch_message(
                    int(post["message_id"])
                )
                await post_message.edit(
                    embed=post_embed(post),
                    view=PostView(self, post["id"], reaction_emoji_ids_saved)
                )
                updated_posts += 1
            except (discord.NotFound, discord.Forbidden, discord.HTTPException) as exc:
                failed_posts.append(post.get("id", post["message_id"]))
                print(
                    f"[Feed] Gagal memperbarui ikon pada postingan "
                    f"{post.get('id', post['message_id'])}: {exc}"
                )

        result = (
            f"✅ Feed disiapkan di {channel.mention}\n"
            f"🧾 Log: {log_channel.mention}\n"
            f"Ikon Like/Dislike dari aset Feed diterapkan ke "
            f"{updated_posts} postingan lama.\n"
            f"{panel_message.jump_url}"
        )
        if failed_posts:
            result += (
                f"\n⚠️ {len(failed_posts)} postingan lama tidak dapat diperbarui. "
                "Periksa izin bot dan channel postingan tersebut."
            )

        await interaction.followup.send(
            result,
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
