import discord
from discord import app_commands
from discord.ext import commands
from bot.store import read, write
from bot.commands.automasi.common import DEFAULT

def configs():
    return read("autothread.json", [], feature="autothread")


class AutoThreadCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="autothread",
        description="Tambah atau hapus Auto Thread"
    )
    @app_commands.default_permissions(
        manage_channels=True
    )
    @app_commands.describe(
        aksi="Pilih aksi: tambah, hapus, atau lihat daftar Auto Thread",
        channel="Channel target (wajib untuk tambah/hapus)",
        reaksi="Satu atau lebih emoji, dipisahkan dengan spasi"
    )
    @app_commands.choices(
        aksi=[
            app_commands.Choice(
                name="Menambahkan (Add)",
                value="tambah"
            ),
            app_commands.Choice(
                name="Menghapus (Remove)",
                value="hapus"
            ),
            app_commands.Choice(
                name="Daftar Autothread (List)",
                value="daftar"
            )
        ]
    )
    async def autothread(
        self,
        i: discord.Interaction,
        aksi: app_commands.Choice[str],
        channel: discord.TextChannel | None = None,
        reaksi: str = ""
    ):
        if not i.guild:
            return await i.response.send_message(
                "Perintah ini hanya dapat digunakan di dalam server.",
                ephemeral=True
            )

        data = configs()

        if aksi.value == "daftar":
            rows = []
            for item in data:
                channel_id = item.get("channelId")
                if not channel_id:
                    continue
                target = i.guild.get_channel(int(channel_id))
                if not isinstance(target, discord.TextChannel):
                    continue
                if item.get("guildId") and item["guildId"] != str(i.guild.id):
                    continue
                rows.append(
                    (
                        target,
                        item.get("threadName", DEFAULT),
                        item.get("reactions", [])
                    )
                )

            embed = discord.Embed(
                title="📋 Daftar Auto Thread",
                description=(
                    f"Total channel terdaftar: **{len(rows)}**"
                    if rows
                    else "Belum ada channel yang menggunakan Auto Thread."
                ),
                color=discord.Color.from_rgb(154, 185, 195)
            )
            for target, thread_name, reactions in rows[:25]:
                value = (
                    f"**Nama Thread:** {thread_name}\n"
                    f"**Auto Reaction:** {' '.join(reactions) or 'Tidak ada'}"
                )
                if len(value) > 180:
                    value = f"{value[:177]}..."
                embed.add_field(
                    name=target.mention,
                    value=value,
                    inline=False
                )
            if len(rows) > 25:
                embed.set_footer(
                    text=f"Menampilkan 25 dari {len(rows)} channel."
                )
            await i.response.send_message(embed=embed, ephemeral=True)
            return

        if channel is None:
            return await i.response.send_message(
                "Pilih `channel` untuk aksi menambahkan atau menghapus Auto Thread.",
                ephemeral=True
            )
        if channel.guild.id != i.guild.id:
            return await i.response.send_message(
                "Channel target harus berada di server ini.",
                ephemeral=True
            )

        old = next(
            (
                x for x in data
                if x.get("channelId") == str(channel.id)
            ),
            None
        )

        # TAMBAH AUTOTHREAD
        if aksi.value == "tambah":
            if old:
                return await i.response.send_message(
                    "⚠️ Channel tersebut sudah menggunakan "
                    "Auto Thread.",
                    ephemeral=True
                )

            reactions = reaksi.split()

            data.append({
                "guildId": str(i.guild.id),
                "channelId": str(channel.id),
                "threadName": DEFAULT,
                "reactions": reactions
            })

            write("autothread.json", data, feature="autothread")

            return await i.response.send_message(
                "✅ **Auto Thread berhasil ditambahkan!**\n\n"
                f"**Channel:** {channel.mention}\n"
                f"**Nama Thread:** {DEFAULT}\n"
                f"**Auto Reaction:** "
                f"{' '.join(reactions) or 'Tidak ada'}",
                ephemeral=True
            )

        # HAPUS AUTOTHREAD
        if not old:
            return await i.response.send_message(
                "⚠️ Channel tersebut belum terdaftar "
                "di Auto Thread.",
                ephemeral=True
            )

        data = [
            x for x in data
            if x.get("channelId") != str(channel.id)
        ]

        write("autothread.json", data, feature="autothread")

        await i.response.send_message(
            f"✅ Auto Thread berhasil dihapus dari {channel.mention}.",
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if (
            not message.guild
            or message.author.bot
            or not isinstance(
                message.channel,
                discord.TextChannel
            )
        ):
            return

        cfg = next(
            (
                x for x in configs()
                if x.get("channelId")
                == str(message.channel.id)
            ),
            None
        )

        if not cfg:
            return

        try:
            await message.create_thread(
                name=cfg.get("threadName", DEFAULT),
                auto_archive_duration=1440,
                reason="Auto Thread Homi"
            )
        except discord.HTTPException as ex:
            print(
                "Gagal membuat Auto Thread:",
                ex
            )
            return

        for emoji in cfg.get("reactions", []):
            try:
                await message.add_reaction(emoji)
            except discord.HTTPException as ex:
                print(
                    f"Gagal menambahkan reaksi "
                    f"{emoji}: {ex}"
                )

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoThreadCog(bot))
