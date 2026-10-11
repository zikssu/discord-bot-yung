import discord
from discord import app_commands
from discord.ext import commands
from bot.store import read, write
from bot.commands.automasi.common import BANNER_URL
from datetime import datetime
import uuid
import asyncio
import aiohttp
from io import BytesIO

MIC_THREAD_NAME = "💬 Comment Section"

def mic_cards():
    return read("mic.json", [], feature="mic")

def save_mic_cards(data):
    write("mic.json", data, feature="mic")

def mic_settings():
    return read("mic_settings.json", [], feature="mic")

def save_mic_settings(data):
    write("mic_settings.json", data, feature="mic")

def format_date_id(value):
    """Format tanggal menjadi gaya Indonesia, contoh: 02 Oktober 2026."""
    months = (
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember",
    )

    if not value:
        return "-"

    if isinstance(value, datetime):
        return f"{value.day:02d} {months[value.month - 1]} {value.year}"

    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            parsed = datetime.strptime(text, fmt)
            return f"{parsed.day:02d} {months[parsed.month - 1]} {parsed.year}"
        except ValueError:
            continue

    return text

def render_mic(data, avatar_bytes):
    """Generate MIC bertema home. dengan Pillow tanpa template gambar eksternal."""
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    import random

    WIDTH, HEIGHT = 1600, 900

    # Palet MIC: kombinasi warna yang baru sesuai referensi komunitas.
    MIST = (154, 185, 195, 255)
    FOREST = (44, 51, 49, 255)
    NIGHT = (35, 36, 41, 255)
    MOSS = (71, 81, 69, 255)
    MUTED = (109, 134, 138, 255)
    FOG = (216, 222, 219, 255)

    SKY_TOP = NIGHT
    SKY_BOTTOM = FOREST
    FIELD_DARK = FOREST
    FIELD = MOSS
    FIELD_LIGHT = MIST
    EARTH = FOREST
    CREAM = FOG
    GOLD = MUTED
    GREEN = MOSS
    GREEN_DARK = FOREST
    PANEL = NIGHT
    PANEL_2 = FOREST
    BORDER = MOSS
    WHITE = FOG

    image = Image.new("RGBA", (WIDTH, HEIGHT), SKY_TOP)
    draw = ImageDraw.Draw(image)

    # Langit: gradien hijau kebiruan seperti sore di kampung.
    for y in range(HEIGHT):
        ratio = min(y / 610, 1.0)
        r = round(SKY_TOP[0] * (1 - ratio) + SKY_BOTTOM[0] * ratio)
        g = round(SKY_TOP[1] * (1 - ratio) + SKY_BOTTOM[1] * ratio)
        b = round(SKY_TOP[2] * (1 - ratio) + SKY_BOTTOM[2] * ratio)
        draw.line((0, y, WIDTH, y), fill=(r, g, b, 255))

    # Matahari sore dan glow lembut.
    sun_x, sun_y, sun_r = 1320, 155, 92
    for r in range(180, sun_r, -8):
        alpha = max(5, int(26 * (180 - r) / 90))
        draw.ellipse((sun_x-r, sun_y-r, sun_x+r, sun_y+r), fill=(*GOLD[:3], alpha))
    draw.ellipse((sun_x-sun_r, sun_y-sun_r, sun_x+sun_r, sun_y+sun_r), fill=GOLD)

    # Siluet perbukitan.
    draw.polygon(
        [(0, 525), (180, 445), (350, 510), (520, 420), (720, 515),
         (900, 430), (1090, 505), (1260, 415), (1450, 500), (1600, 430),
         (1600, 900), (0, 900)],
        fill=(24, 70, 52, 255),
    )
    draw.polygon(
        [(0, 600), (180, 535), (370, 585), (570, 515), (760, 590),
         (980, 525), (1190, 585), (1400, 515), (1600, 570),
         (1600, 900), (0, 900)],
        fill=FIELD_DARK,
    )

    # Sawah berpetak di bagian bawah.
    field_y = 675
    draw.rectangle((0, field_y, WIDTH, HEIGHT), fill=FIELD)
    for y in (720, 765, 810, 855):
        draw.line((0, y, WIDTH, y-22), fill=FIELD_LIGHT, width=3)
    for x in range(-100, WIDTH + 250, 230):
        draw.line((x, field_y, x + 120, HEIGHT), fill=(62, 127, 69, 255), width=4)

    # Pematang sawah.
    draw.line((0, 690, WIDTH, 640), fill=EARTH, width=10)
    draw.line((0, 691, WIDTH, 641), fill=(120, 94, 57, 255), width=3)

    # Siluet rumah kampung di kejauhan.
    def house(x, y, scale=1.0):
        w = int(100 * scale)
        h = int(70 * scale)
        roof_h = int(48 * scale)
        wall = (112, 83, 55, 255)
        roof = (73, 55, 42, 255)
        draw.rectangle((x, y-h, x+w, y), fill=wall)
        draw.polygon([(x-12*scale, y-h), (x+w/2, y-h-roof_h), (x+w+12*scale, y-h)], fill=roof)
        draw.rectangle((x+w*0.42, y-h*0.52, x+w*0.60, y), fill=(57, 48, 39, 255))

    house(1090, 660, 0.9)
    house(1235, 635, 0.7)
    house(1380, 665, 0.85)

    # Pohon sederhana di sisi kanan untuk memperkuat nuansa kampung.
    for tx, ty, scale in ((1015, 625, 1.0), (1510, 620, 1.15), (940, 650, 0.72)):
        trunk_w = int(16 * scale)
        draw.rectangle((tx-trunk_w//2, ty-85*scale, tx+trunk_w//2, ty), fill=(72, 56, 39, 255))
        for ox, oy, rr in ((0,-105,48),(-30,-82,38),(32,-82,40),(0,-70,44)):
            rr = int(rr*scale)
            cx, cy = tx+int(ox*scale), ty+int(oy*scale)
            draw.ellipse((cx-rr, cy-rr, cx+rr, cy+rr), fill=(31, 102, 58, 255))

    # Bingkai kartu.
    draw.rounded_rectangle((26, 26, WIDTH-26, HEIGHT-26), radius=30, fill=(12, 37, 36, 215), outline=BORDER, width=3)
    draw.rounded_rectangle((48, 48, WIDTH-48, HEIGHT-48), radius=22, outline=(62, 108, 85, 255), width=2)

    # Panel utama transparan agar background kampung tetap terlihat.
    draw.rounded_rectangle((62, 190, 1538, 780), radius=28, fill=PANEL, outline=(72, 112, 91, 220), width=2)

    # Dekorasi kecil seperti titik cahaya/lentera, bukan bintang sci-fi.
    seed = sum(ord(char) for char in str(data.get("id", "KIW")))
    rng = random.Random(seed)
    for _ in range(24):
        x = rng.randint(80, WIDTH-80)
        y = rng.randint(70, 620)
        r = rng.choice((2, 2, 3))
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(239, 220, 155, rng.randint(70, 150)))

    font_candidates = {
        "regular": (
            "assets/fonts/Poppins-Regular.ttf",
            "assets/fonts/DejaVuSans.ttf",
            "assets/fonts/NotoSans-Regular.ttf",
        ),
        "bold": (
            "assets/fonts/Poppins-Bold.ttf",
            "assets/fonts/DejaVuSans-Bold.ttf",
            "assets/fonts/NotoSans-Bold.ttf",
        ),
        "mono": (
            "assets/fonts/DejaVuSansMono-Bold.ttf",
            "assets/fonts/DejaVuSansMono.ttf",
        ),
    }

    def font(size, kind="regular"):
        for candidate in font_candidates[kind]:
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                continue
        return ImageFont.load_default()

    def fit_text(text, fnt, max_width):
        value = str(text or "-").strip() or "-"
        if draw.textbbox((0, 0), value, font=fnt)[2] <= max_width:
            return value
        while len(value) > 1 and draw.textbbox((0, 0), value + "…", font=fnt)[2] > max_width:
            value = value[:-1]
        return value.rstrip() + "…"

    def centered_text(text, box, fnt, fill):
        x1, y1, x2, y2 = box
        bbox = draw.textbbox((0, 0), text, font=fnt)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        tx = x1 + ((x2-x1)-tw)/2 - bbox[0]
        ty = y1 + ((y2-y1)-th)/2 - bbox[1]
        draw.text((tx, ty), text, font=fnt, fill=fill)

    def rounded_field(x, y, w, h, label, value):
        # Area petunjuk kiri dibuat tetap sama untuk semua kolom.
        # Jika label panjang seperti "JENIS KELAMIN", ukuran font
        # otomatis diperkecil agar tidak melewati batas area.
        label_font = font(30, "bold")
        value_font = font(34, "bold")

        field_x = x + 235
        field_w = w - 235
        label_max_width = field_x - x - 18

        while (
            draw.textbbox((0, 0), str(label), font=label_font)[2]
            > label_max_width
            and getattr(label_font, "size", 30) > 22
        ):
            label_font = font(getattr(label_font, "size", 30) - 1, "bold")

        # Input field.
        draw.rounded_rectangle(
            (field_x, y, field_x + field_w, y + h),
            radius=14,
            fill=PANEL_2,
            outline=(91, 121, 101, 230),
            width=2,
        )

        # Label dipusatkan secara vertikal terhadap input field,
        # sehingga semua petunjuk kiri sejajar dengan kolom pengisian.
        label_bbox = draw.textbbox((0, 0), label, font=label_font)
        label_h = label_bbox[3] - label_bbox[1]
        label_y = y + (h - label_h) / 2 - label_bbox[1]
        draw.text((x, label_y), label, font=label_font, fill=WHITE)

        # Value dipusatkan secara vertikal terhadap input field.
        value = fit_text(value, value_font, field_w - 42)
        bbox = draw.textbbox((0, 0), value, font=value_font)
        text_h = bbox[3] - bbox[1]
        ty = y + (h - text_h) / 2 - bbox[1]
        draw.text((field_x + 20, ty), value, font=value_font, fill=WHITE)

    # Header.
    draw.text((80, 68), "KARTU IDENTITAS PENGHUNI", font=font(58, "mono"), fill=WHITE)
    draw.text((82, 138), "HOME.", font=font(25, "bold"), fill=GOLD)

    card_number = str(data.get("card_number", "MIC-00000"))
    draw.rounded_rectangle((1235, 78, 1518, 132), radius=27, fill=GREEN_DARK, outline=GOLD, width=2)
    centered_text(card_number, (1240, 80, 1513, 130), font(21, "mono"), WHITE)

    # Avatar profil Discord.
    # Ukuran diperkecil agar proporsional dengan layout kartu dan tidak mendominasi isi MIC.
    # Profil avatar dipusatkan di area kiri setelah teks di bawah avatar dihapus.
    avatar_box = (108, 260, 468, 690)
    avatar_size = 320
    avatar_center = ((avatar_box[0] + avatar_box[2]) // 2, (avatar_box[1] + avatar_box[3]) // 2)

    ring_padding = 8
    ring_box = (
        avatar_center[0] - avatar_size // 2 - ring_padding,
        avatar_center[1] - avatar_size // 2 - ring_padding,
        avatar_center[0] + avatar_size // 2 + ring_padding,
        avatar_center[1] + avatar_size // 2 + ring_padding,
    )
    draw.ellipse(ring_box, fill=(28, 93, 62, 255), outline=GOLD, width=4)

    avatar_ok = False
    if avatar_bytes:
        try:
            avatar = Image.open(BytesIO(avatar_bytes)).convert("RGBA")
            avatar = ImageOps.fit(
                avatar,
                (avatar_size, avatar_size),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )

            mask = Image.new("L", (avatar_size, avatar_size), 0)
            ImageDraw.Draw(mask).ellipse(
                (0, 0, avatar_size - 1, avatar_size - 1),
                fill=255,
            )

            avatar_x = avatar_center[0] - avatar_size // 2
            avatar_y = avatar_center[1] - avatar_size // 2
            image.paste(avatar, (avatar_x, avatar_y), mask)
            avatar_ok = True
        except Exception as avatar_error:
            print(f"[MIC] Gagal memproses gambar avatar: {avatar_error}")

    if not avatar_ok:
        # Hanya gunakan inisial jika Discord/CDN benar-benar tidak menyediakan gambar.
        initials = "".join(
            part[0]
            for part in str(data.get("display_name") or data.get("name") or "W").split()[:2]
        ).upper()
        centered_text(
            initials or "W",
            avatar_box,
            font(64, "bold"),
            CREAM,
        )

    # Data identitas.
    rounded_field(570, 215, 940, 72, "NAMA", data.get("name", "-"))
    rounded_field(570, 310, 940, 72, "UMUR", f"{data.get('age', '-')} Tahun")
    rounded_field(570, 405, 940, 72, "JENIS KELAMIN", data.get("gender", "-"))
    rounded_field(570, 500, 940, 72, "DOMISILI", data.get("domicile", "-"))
    rounded_field(570, 595, 940, 72, "HOBI", data.get("hobby", "-"))

    # Hanya tanggal bergabung di bagian metadata; STATUS WARGA dihapus.
    draw.text((570, 690), "BERGABUNG", font=font(22, "bold"), fill=MUTED)
    joined = fit_text(format_date_id(data.get("joined_at")), font(25, "bold"), 360)
    draw.text((570, 724), joined, font=font(25, "bold"), fill=WHITE)

    # Footer identitas komunitas.
    footer = "Member Identity Card (MIC)"
    centered_text(footer, (1010, 685, 1515, 735), font(20, "bold"), GOLD)
    centered_text("Data member melalui sistem komunitas", (1010, 725, 1515, 765), font(16), MUTED)

    # Tidak ada progress bar / loading bar di bagian bawah.
    output = BytesIO()
    image.convert("RGB").save(output, format="PNG", optimize=True)
    output.seek(0)
    return output

class MICModal(discord.ui.Modal):
    def __init__(self, cog, mode="create", existing=None):
        super().__init__(title="Buat Kartu Identitas" if mode == "create" else "Edit Kartu Identitas")
        self.cog = cog
        self.mode = mode
        existing = existing or {}

        self.name_input = discord.ui.TextInput(
            label="Nama",
            placeholder="Masukkan Nama kamu...",
            default=existing.get("name", "") or None,
            max_length=80,
            required=True,
        )
        self.age_input = discord.ui.TextInput(
            label="Umur",
            placeholder="Contohnya umur kamu itu 13.",
            default=str(existing.get("age", "")) or None,
            max_length=3,
            required=True,
        )
        self.gender_input = discord.ui.TextInput(
            label="Jenis Kelamin",
            placeholder="Pria / Wanita",
            default=existing.get("gender", "") or None,
            max_length=30,
            required=True,
        )
        self.domicile_input = discord.ui.TextInput(
            label="Domisili",
            placeholder="Contohnya: Pekanbaru, Riau",
            default=existing.get("domicile", "") or None,
            max_length=100,
            required=True,
        )
        self.hobby_input = discord.ui.TextInput(
            label="Hobi",
            placeholder="Hobi kamu apa? (Opsional)",
            default=existing.get("hobby", "") or None,
            max_length=120,
            required=False,
        )

        for field in (
            self.name_input,
            self.age_input,
            self.gender_input,
            self.domicile_input,
            self.hobby_input,
        ):
            self.add_item(field)

    async def on_submit(self, interaction: discord.Interaction):
        age_text = self.age_input.value.strip()
        if not age_text.isdigit() or not 1 <= int(age_text) <= 120:
            return await interaction.response.send_message(
                "❌ Umur harus berupa angka antara 1 sampai 120.",
                ephemeral=True,
            )

        values = {
            "name": self.name_input.value.strip(),
            "age": int(age_text),
            "gender": self.gender_input.value.strip(),
            "domicile": self.domicile_input.value.strip(),
            "hobby": self.hobby_input.value.strip() or "-",
        }

        if not values["name"] or not values["gender"] or not values["domicile"]:
            return await interaction.response.send_message(
                "❌ Nama, jenis kelamin, dan domisili wajib diisi.",
                ephemeral=True,
            )

        await self.cog.save_mic(interaction, values, self.mode)

class MICPanelView(discord.ui.View):
    """Persistent buttons for the main  setup panel."""

    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    def _find_user_card(self, interaction):
        return next(
            (
                item for item in mic_cards()
                if item.get("guild_id") == str(interaction.guild_id)
                and item.get("user_id") == str(interaction.user.id)
            ),
            None,
        )

    @discord.ui.button(
        label="Buat MIC",
        emoji="🪪",
        style=discord.ButtonStyle.primary,
        custom_id="mic:panel:create",
    )
    async def create_mic(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild:
            return await interaction.response.send_message(
                "Fitur ini hanya dapat digunakan di server.", ephemeral=True
            )

        existing = self._find_user_card(interaction)
        if existing:
            return await interaction.response.send_message(
                "⚠️ Kamu sudah memiliki MIC. Gunakan tombol **Melihat MIC** "
                "untuk melihat kartu atau **Edit** pada kartu untuk memperbaruinya.",
                ephemeral=True,
            )

        try:
            await interaction.response.send_modal(MICModal(self.cog, "create"))
        except discord.HTTPException as exc:
            print(f"[MIC] Gagal membuka modal Buat MIC: {exc}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Form MIC gagal dibuka. Silakan coba lagi.", ephemeral=True
                )

    @discord.ui.button(
        label="Lihat MIC",
        emoji="👁️",
        style=discord.ButtonStyle.secondary,
        custom_id="mic:panel:view",
    )
    async def view_mic(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild:
            return await interaction.response.send_message(
                "Fitur ini hanya dapat digunakan di server.", ephemeral=True
            )

        card = self._find_user_card(interaction)
        if not card:
            return await interaction.response.send_message(
                "ℹ️ Kamu belum memiliki MIC. Silakan tekan **Buat MIC** terlebih dahulu.",
                ephemeral=True,
            )

        message_id = card.get("message_id")
        if not message_id:
            return await interaction.response.send_message(
                "⚠️ Data MIC ditemukan, tetapi pesan kartunya tidak tersedia. "
                "Silakan hubungi admin untuk memperbaikinya.",
                ephemeral=True,
            )

        channel_id = card.get("channel_id")
        channel = interaction.guild.get_channel(int(channel_id)) if channel_id else None
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                "⚠️ Channel MIC tidak ditemukan. Minta admin menjalankan `/setup-mic` ulang.",
                ephemeral=True,
            )

        try:
            message = await channel.fetch_message(int(message_id))
        except discord.NotFound:
            return await interaction.response.send_message(
                "⚠️ Pesan MIC kamu sudah tidak ditemukan. Minta admin membuat ulang panel MIC.",
                ephemeral=True,
            )
        except discord.HTTPException as exc:
            print(f"[MIC] Gagal mengambil pesan kartu: {exc}")
            return await interaction.response.send_message(
                "❌ Kartu MIC gagal diambil. Silakan coba lagi.", ephemeral=True
            )

        await interaction.response.send_message(
            f"🪪 **MIC kamu:** {message.jump_url}", ephemeral=True
        )

class MICCardView(discord.ui.View):
    """Persistent buttons attached to every generated MIC card."""

    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    async def _get_card(self, interaction):
        return next(
            (
                item for item in mic_cards()
                if item.get("guild_id") == str(interaction.guild_id)
                and item.get("message_id") == str(interaction.message.id)
            ),
            None,
        )

    def _find_user_card(self, interaction):
        return next(
            (
                item for item in mic_cards()
                if item.get("guild_id") == str(interaction.guild_id)
                and item.get("user_id") == str(interaction.user.id)
            ),
            None,
        )

    @discord.ui.button(
        label="Buat MIC",
        emoji="🪪",
        style=discord.ButtonStyle.primary,
        custom_id="mic:card:create",
    )
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild:
            return await interaction.response.send_message(
                "Fitur ini hanya dapat digunakan di server.", ephemeral=True
            )

        existing = self._find_user_card(interaction)
        if existing:
            return await interaction.response.send_message(
                "⚠️ Kamu sudah memiliki MIC. Gunakan **Lihat MIC** atau **Edit**.",
                ephemeral=True,
            )

        try:
            await interaction.response.send_modal(MICModal(self.cog, "create"))
        except discord.HTTPException as exc:
            print(f"[MIC] Gagal membuka modal dari kartu: {exc}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Form MIC gagal dibuka. Silakan coba lagi.", ephemeral=True
                )

    @discord.ui.button(
        label="Lihat MIC",
        emoji="👁️",
        style=discord.ButtonStyle.secondary,
        custom_id="mic:card:view",
    )
    async def view(self, interaction: discord.Interaction, button: discord.ui.Button):
        card = self._find_user_card(interaction)
        if not card:
            return await interaction.response.send_message(
                "ℹ️ Kamu belum memiliki MIC. Silakan tekan **Buat MIC** terlebih dahulu.",
                ephemeral=True,
            )

        message_id = card.get("message_id")
        channel_id = card.get("channel_id")
        if not message_id or not channel_id or not interaction.guild:
            return await interaction.response.send_message(
                "⚠️ Data pesan MIC tidak lengkap.", ephemeral=True
            )

        channel = interaction.guild.get_channel(int(channel_id))
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                "⚠️ Channel MIC tidak ditemukan.", ephemeral=True
            )

        try:
            message = await channel.fetch_message(int(message_id))
        except discord.HTTPException as exc:
            print(f"[MIC] Gagal mengambil MIC: {exc}")
            return await interaction.response.send_message(
                "❌ MIC gagal diambil. Silakan coba lagi.", ephemeral=True
            )

        await interaction.response.send_message(
            f"🪪 **MIC kamu:** {message.jump_url}", ephemeral=True
        )

    @discord.ui.button(
        label="Edit",
        emoji="✏️",
        style=discord.ButtonStyle.secondary,
        custom_id="mic:card:edit",
    )
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        card = await self._get_card(interaction)
        if not card:
            return await interaction.response.send_message(
                "Data MIC tidak ditemukan.", ephemeral=True
            )
        if card.get("user_id") != str(interaction.user.id):
            return await interaction.response.send_message(
                "Kamu hanya dapat Mengedit MIC Milikmu sendiri.", ephemeral=True
            )
        try:
            await interaction.response.send_modal(MICModal(self.cog, "edit", card))
        except discord.HTTPException as exc:
            print(f"[MIC] Gagal membuka modal edit: {exc}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Form Edit MIC gagal dibuka. Silakan coba lagi.", ephemeral=True
                )

    @discord.ui.button(
        label="Hapus",
        emoji="🗑️",
        style=discord.ButtonStyle.danger,
        custom_id="mic:card:delete",
    )
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        card = await self._get_card(interaction)
        if not card:
            return await interaction.response.send_message(
                "Data MIC tidak ditemukan.", ephemeral=True
            )
        if card.get("user_id") != str(interaction.user.id):
            return await interaction.response.send_message(
                "Kamu hanya dapat Menghapus MIC Milikmu sendiri.", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True, thinking=True)
        data = [item for item in mic_cards() if item.get("id") != card.get("id")]
        save_mic_cards(data)

        if interaction.message:
            try:
                await interaction.message.delete()
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass

        thread_id = card.get("thread_id")
        if thread_id and interaction.guild:
            thread = interaction.guild.get_thread(int(thread_id))
            if thread:
                try:
                    await thread.delete(reason="MIC dihapus oleh pemilik kartu")
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    pass

        await interaction.followup.send(
            "✅ Kartu Identity Card (MIC) berhasil dihapus.", ephemeral=True
        )

class MICCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="setup-mic",
        description="Menyiapkan panel Member Identity Card (MIC)",
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(channel="Channel untuk panel Member Identity Card (MIC)")
    async def setup_mic(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.guild:
            return await interaction.response.send_message(
                "Gunakan perintah ini di dalam server.", ephemeral=True
            )

        # Ack lebih dulu agar slash command tidak menjadi Interaction Failed
        # ketika Discord membutuhkan waktu untuk mengirim panel ke channel.
        await interaction.response.defer(ephemeral=True, thinking=True)

        panel = discord.Embed(
            description=(
                "# 🪪 Member Identity Card\nKenali member, bangun kebersamaan, dalam satu identitas.\n\n"
                "Tekan **Buat MIC** untuk mengisi identitas member home.. "
                "Setiap member dapat membuat satu kartu, lalu memperbarui atau "
                "menghapusnya melalui tombol pada kartu masing-masing."
            ),
            color=discord.Color.from_rgb(154, 185, 195),
        )
        panel.set_image(url=BANNER_URL)

        try:
            posted = await channel.send(embed=panel, view=MICPanelView(self))
        except discord.Forbidden:
            return await interaction.followup.send(
                "Bot tidak memiliki izin mengirim pesan/embed ke channel tersebut.",
                ephemeral=True,
            )

        configs = [
            item for item in mic_settings()
            if item.get("guild_id") != str(interaction.guild_id)
        ]
        configs.append({
            "guild_id": str(interaction.guild_id),
            "channel_id": str(channel.id),
            "panel_message_id": str(posted.id),
        })
        save_mic_settings(configs)

        await interaction.followup.send(
            f"✅ Panel MIC berhasil disiapkan di {channel.mention}.\n"
            f"[Lihat panel]({posted.jump_url})",
            ephemeral=True,
        )

    async def save_mic(self, interaction: discord.Interaction, values: dict, mode: str):
        if not interaction.guild:
            return await interaction.response.send_message(
                "Fitur ini hanya dapat digunakan di server.", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True, thinking=True)
        all_cards = mic_cards()
        card = next(
            (item for item in all_cards
             if item.get("guild_id") == str(interaction.guild_id)
             and item.get("user_id") == str(interaction.user.id)),
            None,
        )

        if mode == "create" and card:
            return await interaction.followup.send(
                "Kamu sudah memiliki MIC. Gunakan tombol Edit.", ephemeral=True
            )
        if mode == "edit" and not card:
            return await interaction.followup.send(
                "MIC kamu belum ditemukan. Buat kartu baru melalui panel.", ephemeral=True
            )

        cfg = next(
            (item for item in mic_settings()
             if item.get("guild_id") == str(interaction.guild_id)),
            None,
        )
        if not cfg:
            return await interaction.followup.send(
                "Panel MIC belum disiapkan administrator dengan `/setup-mic`.",
                ephemeral=True,
            )
        channel = interaction.guild.get_channel(int(cfg["channel_id"]))
        if not isinstance(channel, discord.TextChannel):
            return await interaction.followup.send(
                "Channel MIC tidak ditemukan. Minta tolong Admin menjalankan setup ulang.",
                ephemeral=True,
            )

        if card is None:
            next_number = 1 + max(
                (int(item.get("number", 0)) for item in all_cards
                 if item.get("guild_id") == str(interaction.guild_id)),
                default=0,
            )
            card = {
                "id": uuid.uuid4().hex[:12],
                "guild_id": str(interaction.guild_id),
                "user_id": str(interaction.user.id),
                "number": next_number,
                "card_number": f"MIC-{next_number:05d}",
                "message_id": None,
                "thread_id": None,
                "channel_id": str(channel.id),
                "joined_at": format_date_id(getattr(interaction.user, "joined_at", None) or discord.utils.utcnow()),
                "status": "Member Aktif",
                "privacy": "Publik",
            }

        card.update(values)
        card["channel_id"] = str(channel.id)
        card["display_name"] = interaction.user.display_name
        card["avatar_url"] = interaction.user.display_avatar.url

        try:
            # Avatar Discord dapat gagal diambil (misalnya asset 404).
            # Jika gagal, renderer tetap membuat kartu dengan placeholder avatar.
            # Ambil avatar dari data Discord yang FRESH.
            # Interaction.user bisa berisi Asset/hash lama setelah user
            # mengganti foto profil. Kita fetch ulang User dari Discord API
            # sebelum membaca CDN avatar.
            avatar_bytes = None

            fresh_user = interaction.user
            try:
                fresh_user = await self.bot.fetch_user(interaction.user.id)
                print("[MIC] Data profil Discord berhasil diperbarui.")
            except Exception as fetch_error:
                print(
                    f"[MIC] Gagal mengambil profil terbaru: "
                    f"{type(fetch_error).__name__}: {fetch_error}"
                )

            avatar_candidates = []

            # Ambil Member terbaru terlebih dahulu agar avatar khusus server
            # (jika ada) ikut diprioritaskan.
            fresh_member = None
            if interaction.guild is not None:
                try:
                    fresh_member = await interaction.guild.fetch_member(
                        interaction.user.id
                    )
                    member_display_avatar = getattr(
                        fresh_member, "display_avatar", None
                    )
                    if member_display_avatar is not None:
                        avatar_candidates.append(
                            ("server/member display avatar (fresh)", member_display_avatar)
                        )

                    fresh_guild_avatar = getattr(
                        fresh_member, "guild_avatar", None
                    )
                    if fresh_guild_avatar is not None:
                        avatar_candidates.append(
                            ("server avatar (fresh)", fresh_guild_avatar)
                        )
                except Exception as member_error:
                    print(
                        f"[MIC] Gagal mengambil profil server terbaru: "
                        f"{type(member_error).__name__}: {member_error}"
                    )

            # Display avatar dari User hasil fetch: custom avatar jika ada,
            # atau default avatar jika tidak memiliki avatar custom.
            fresh_display_avatar = getattr(
                fresh_user, "display_avatar", None
            )
            if fresh_display_avatar is not None:
                avatar_candidates.append(
                    ("user display avatar (fresh)", fresh_display_avatar)
                )

            # Tambahkan avatar global mentah sebagai alternatif.
            fresh_profile_avatar = getattr(fresh_user, "avatar", None)
            if fresh_profile_avatar is not None:
                avatar_candidates.append(
                    ("profile avatar (fresh)", fresh_profile_avatar)
                )

            # Fallback ke objek user/member dari interaction bila fetch
            # mengembalikan asset yang tidak dapat dibaca.
            interaction_display_avatar = getattr(
                interaction.user, "display_avatar", None
            )
            if interaction_display_avatar is not None:
                avatar_candidates.append(
                    ("interaction display avatar", interaction_display_avatar)
                )

            if interaction.guild is not None:
                interaction_guild_avatar = getattr(
                    interaction.user, "guild_avatar", None
                )
                if interaction_guild_avatar is not None:
                    avatar_candidates.append(
                        ("interaction server avatar", interaction_guild_avatar)
                    )

            # Default avatar Discord menjadi fallback terakhir.
            default_avatar = getattr(fresh_user, "default_avatar", None)
            if default_avatar is not None:
                avatar_candidates.append(
                    ("default avatar", default_avatar)
                )

            attempted_urls = set()
            for avatar_label, avatar_asset in avatar_candidates:
                if avatar_bytes:
                    break
                try:
                    # Discord Asset dapat berupa GIF/WEBP/PNG. Paksa PNG untuk
                    # menghindari renderer Pillow gagal membaca format tertentu.
                    asset_variants = [avatar_asset]
                    try:
                        asset_variants.append(avatar_asset.replace(format="png", size=512))
                    except Exception:
                        pass
                    try:
                        asset_variants.append(avatar_asset.with_size(512))
                    except Exception:
                        pass

                    for variant in asset_variants:
                        try:
                            asset_url = getattr(variant, "url", None)
                            if asset_url and asset_url in attempted_urls:
                                continue
                            if asset_url:
                                attempted_urls.add(asset_url)

                            # Jalur pertama: API Asset resmi discord.py.
                            avatar_bytes = await variant.read()
                            if avatar_bytes:
                                print(
                                    f"[MIC] Avatar berhasil diambil: {avatar_label}"
                                    + (f" | {asset_url}" if asset_url else "")
                                )
                                break
                        except Exception as avatar_error:
                            print(
                                f"[MIC] Gagal mengambil {avatar_label}"
                                + (f" | {getattr(variant, 'url', 'URL tidak tersedia')}")
                                + f": {type(avatar_error).__name__}: {avatar_error}"
                            )

                    # Jalur kedua: GET langsung ke CDN dengan query size/format.
                    if not avatar_bytes:
                        base_url = getattr(avatar_asset, "url", None)
                        if base_url:
                            direct_urls = [
                                base_url,
                                base_url.split("?")[0] + "?size=512&format=png",
                                base_url.split("?")[0] + "?size=1024&format=png",
                            ]
                            timeout = aiohttp.ClientTimeout(total=12)
                            async with aiohttp.ClientSession(timeout=timeout) as session:
                                for direct_url in dict.fromkeys(direct_urls):
                                    try:
                                        async with session.get(
                                            direct_url,
                                            headers={"User-Agent": "DiscordBot KIW Avatar"},
                                        ) as response:
                                            if response.status == 200:
                                                payload = await response.read()
                                                if payload:
                                                    avatar_bytes = payload
                                                    print(
                                                        f"[MIC] Avatar berhasil diambil via CDN langsung: {direct_url}"
                                                    )
                                                    break
                                            else:
                                                print(
                                                    f"[MIC] CDN avatar HTTP {response.status}: {direct_url}"
                                                )
                                    except Exception as direct_error:
                                        print(
                                            f"[MIC] Gagal CDN langsung: {type(direct_error).__name__}: {direct_error}"
                                        )
                                    if avatar_bytes:
                                        break
                except Exception as avatar_error:
                    print(
                        f"[MIC] Gagal memproses kandidat {avatar_label}: "
                        f"{type(avatar_error).__name__}: {avatar_error}"
                    )

            if avatar_bytes is None:
                print(
                    "[MIC] Semua sumber avatar Discord gagal. "
                    "Renderer menggunakan fallback. Avatar Discord tetap dipasang "
                    "sebagai thumbnail embed bila URL masih dapat diakses."
                )

            image_buffer = await asyncio.to_thread(
                render_mic, card, avatar_bytes
            )
        except ImportError:
            return await interaction.followup.send(
                "Library Pillow belum terpasang. Jalankan `pip install Pillow`.",
                ephemeral=True,
            )
        except Exception as exc:
            return await interaction.followup.send(
                f"Gagal membuat gambar MIC: `{type(exc).__name__}: {exc}`",
                ephemeral=True,
            )

        file = discord.File(image_buffer, filename="mic.png")
        embed = discord.Embed(
            description=f"🪪 **Member Identity Card** {interaction.user.mention}",
            color=discord.Color.from_rgb(154, 185, 195),
        )
        embed.set_image(url="attachment://mic.png")

        try:
            if card.get("message_id"):
                try:
                    message = await channel.fetch_message(int(card["message_id"]))
                    await message.edit(embed=embed, attachments=[file], view=MICCardView(self))
                except discord.NotFound:
                    card["message_id"] = None

            if not card.get("message_id"):
                message = await channel.send(embed=embed, file=file, view=MICCardView(self))
                card["message_id"] = str(message.id)
                thread = await message.create_thread(
                    name=MIC_THREAD_NAME,
                    auto_archive_duration=1440,
                    reason="Kolom komentar Member Identity Card (MIC)",
                )
                card["thread_id"] = str(thread.id)
        except discord.Forbidden:
            return await interaction.followup.send(
                "Bot tidak memiliki izin mengirim/mengedit pesan atau membuat thread. "
                "Periksa Send Messages, Embed Links, Attach Files, Create Public Threads, "
                "dan Send Messages in Threads.",
                ephemeral=True,
            )
        except discord.HTTPException as exc:
            return await interaction.followup.send(
                f"Discord gagal memproses kartu: `{exc}`", ephemeral=True
            )

        if not any(item.get("id") == card["id"] for item in all_cards):
            all_cards.append(card)
        save_mic_cards(all_cards)
        await interaction.followup.send(
            ("✅ MIC berhasil dibuat." if mode == "create" else "✅ MIC berhasil diperbarui.")
            + f"\n🪪 Nomor: **{card['card_number']}**\n"
            + f"📨 [Lihat kartu]({message.jump_url})",
            ephemeral=True,
        )

async def setup(bot: commands.Bot):
    cog = MICCog(bot)
    bot.add_view(MICPanelView(cog))
    bot.add_view(MICCardView(cog))
    await bot.add_cog(cog)
