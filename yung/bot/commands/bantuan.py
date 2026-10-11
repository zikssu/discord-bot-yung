import discord
from discord import app_commands
from discord.ext import commands

BANNER_URL = "https://cdn.discordapp.com/attachments/1556887667969359932/1556914044470960159/banner-server-discord-home-line.png?backend=b2&ex=6ac68d72&is=6ac53bf2&hm=eb936f118322147fa10ff0eb59ac5f73bbecd1c287f854376843a3c86883ca19"

class HelpSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Pilih petunjuk berdasarkan kegunaan...",
            custom_id="bantuan:kategori",
            options=[
                discord.SelectOption(
                    label="Beranda",
                    description="Pengenalan yung dan cara menggunakan bantuan.",
                    value="utama",
                    emoji="🏠"
                ),
                discord.SelectOption(
                    label="Utilitas",
                    description="Informasi server, pengguna, dan koneksi bot.",
                    value="utilitas",
                    emoji="🛠️"
                ),
                discord.SelectOption(
                    label="Administrasi",
                    description="Pengaturan fitur server untuk pengelola.",
                    value="administrasi",
                    emoji="⚙️"
                )
            ]
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=make_embed(self.values[0]),
            view=self.view
        )


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(HelpSelect())


def make_embed(category):
    e = discord.Embed(color=0xffffff)

    if category == "utama":
        e.description = (
            "# H!! Kenalin gue yung.\n"
            "-# Prefix `/` | Mention <@1553311149850628156>\n\n"
            "Gue adalah seorang **All in One Bot** "
            "untuk membantu mengelola, merawat, dan mengembangkan "
            "komunitas **home.**. 🏡\n\n"
            "> Pilih kategori dari menu di bawah untuk melihat command."
        )

    elif category == "utilitas":
        e.description = (
            "# 🛠️ Utilitas\n"
            "Command umum yang dapat digunakan semua anggota.\n\n"
            "- `/infoserver` — Lihat nama, pemilik, jumlah anggota, dan tanggal pembuatan server.\n"
            "- `/infouser` — Lihat profil kamu; isi opsi `pengguna` untuk melihat pengguna lain.\n"
            "- `/ping` — Periksa latensi koneksi bot yung."
        )

    elif category == "administrasi":
        automasi_commands = [
            ("/autothread", "Tambah/hapus Auto Thread, atur banyak reaksi, atau tampilkan daftar dalam embed. — Manage Channels"),
            ("/auto-reminder", "Atur jeda reminder berulang selamanya dan pilih Role yang otomatis di-mention. — Manage Channels"),
        ]
        other_commands = [
            ("/setup-feed", "Siapkan panel Home Feed dan channel log. — Manage Server"),
            ("/setup-mic", "Kirim panel Kartu Identitas Penghuni. — Manage Server"),
            ("/setup-moots", "Kirim panel Moots. — Manage Channels"),
            ("/setup-feedback", "Kirim panel Feedback Box. — Manage Channels"),
            ("/setup-ticket", "Siapkan panel ticket dan channel log ticket. — Manage Channels"),
        ]
        e.description = (
            "# ⚙️ Administrasi Server\n"
            "Command pengaturan untuk staf. Izin yang tercantum adalah izin Discord yang diperlukan.\n\n"
            "**🤖 Automasi**\n"
            + "\n".join(
                f"- `{name}` — {description}"
                for name, description in sorted(automasi_commands)
            )
            + "\n\n**⚙️ Fitur Lainnya**\n"
            + "\n".join(
                f"- `{name}` — {description}"
                for name, description in sorted(other_commands)
            )
        )
        e.description += (
            "\n\n**Petunjuk Auto Reminder**\n"
            "- Pada post, klik kanan atau tekan `⋯` → **Apps** → "
            "**Auto Reminder dari Post**. Link post terisi otomatis; isi "
            "`Jeda Waktu (menit)` dan pilih Role pada `Tag Role` bila perlu.\n"
            "- Melalui `/auto-reminder`, jalankan command langsung di "
            "channel tujuan, pilih `Tambah`, isi `pesan`, atur "
            "`jeda_waktu_menit`, dan pilih `tag` jika ingin me-mention Role.\n"
            "- Contoh jeda: `60` = 1 jam, `1440` = 24 jam. Reminder terus "
            "berulang dengan jeda itu sampai dihapus. Role terpilih akan "
            "di-mention pada setiap pengiriman.\n"
            "- Gunakan `Daftar` untuk melihat ID dan `Hapus` dengan ID "
            "tersebut untuk menghentikan pengingat."
        )

    else:
        e.description = (
            "# Hi! Kenalin gue yung.\n"
            "-# Prefix `/` | Mention <@1553311149850628156>\n\n"
            "Gue adalah seorang **All in One Bot** "
            "untuk membantu mengelola, merawat, dan mengembangkan "
            "komunitas **home.**. 🏡\n\n"
            "> Pilih kategori dari menu di bawah untuk melihat command."
        )

    # Banner home. di bagian bawah embed
    if BANNER_URL:
        e.set_image(url=BANNER_URL)

    return e

class Bantuan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="bantuan",
        description="Menampilkan pusat bantuan Homi"
    )
    async def bantuan(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=make_embed("utama"),
            view=HelpView(),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Bantuan(bot))