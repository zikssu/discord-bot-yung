import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

from bot.store import read, write

AUTO_REMINDER_INTERVAL_MINUTES = 24 * 60

def auto_reminders():
    return read("auto_reminders.json", [], feature="auto_reminder")


def save_auto_reminders(data):
    write("auto_reminders.json", data, feature="auto_reminder")
class AutoReminderPostModal(discord.ui.Modal):
    def __init__(self, cog, message: discord.Message):
        super().__init__(title="Auto Reminder dari Post")
        self.cog = cog
        self.guild_id = message.guild.id
        self.channel_id = message.channel.id
        self.post_link = discord.ui.TextInput(
            default=message.jump_url,
            max_length=1900,
            required=True,
        )
        self.delay_minutes = discord.ui.TextInput(
            default=str(AUTO_REMINDER_INTERVAL_MINUTES),
            placeholder="1440 = 24 jam; contoh 60 = 1 jam",
            max_length=6,
            required=True,
        )
        self.role_select = discord.ui.RoleSelect(
            placeholder="Pilih role untuk di-mention (opsional)",
            min_values=0,
            max_values=1,
            required=False,
        )
        self.add_item(
            discord.ui.Label(
                text="Link Post",
                description="Link post sudah terisi otomatis.",
                component=self.post_link,
            )
        )
        self.add_item(
            discord.ui.Label(
                text="Jeda Waktu (menit)",
                description=(
                    "Interval kirim berulang selamanya. 1440 menit = 24 jam."
                ),
                component=self.delay_minutes,
            )
        )
        self.add_item(
            discord.ui.Label(
                text="Tag Role (opsional)",
                description="Role ini akan di-mention pada setiap reminder.",
                component=self.role_select,
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        link = self.post_link.value.strip()
        if not link:
            return await interaction.response.send_message(
                "Link post tidak boleh kosong.",
                ephemeral=True,
            )

        try:
            delay = int(self.delay_minutes.value.strip())
        except ValueError:
            return await interaction.response.send_message(
                "Jeda Waktu harus berupa angka menit.",
                ephemeral=True,
            )
        if not 1 <= delay <= 525600:
            return await interaction.response.send_message(
                "Jeda Waktu harus antara 1 sampai 525600 menit.",
                ephemeral=True,
            )

        role = self.role_select.values[0] if self.role_select.values else None
        if (
            role is not None
            and not role.mentionable
            and not interaction.app_permissions.mention_everyone
        ):
            return await interaction.response.send_message(
                "Bot tidak dapat mention Role tersebut. Aktifkan opsi "
                "**Allow anyone to mention this role** atau beri bot izin "
                "**Mention @everyone, @here, and All Roles**.",
                ephemeral=True,
            )

        reminder_id = uuid.uuid4().hex[:8]
        reminder = {
            "id": reminder_id,
            "guild_id": str(self.guild_id),
            "channel_id": str(self.channel_id),
            "message": f"🔔 Pengingat post:\n{link}",
            "created_by": str(interaction.user.id),
            "repeat_minutes": delay,
            "tag_role_id": str(role.id) if role else None,
            "next_run_at": (
                datetime.now(timezone.utc)
                + timedelta(minutes=delay)
            ).isoformat(),
        }
        async with self.cog._reminder_lock:
            data = auto_reminders()
            data.append(reminder)
            save_auto_reminders(data)

        await interaction.response.send_message(
            f"✅ Pengingat post `{reminder_id}` disiapkan. "
            f"Post ini akan diingatkan setiap {delay} menit tanpa batas waktu "
            f"di channel/thread asalnya{f' dengan tag {role.mention}' if role else ''}.",
            ephemeral=True,
        )


class AutoReminderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._reminder_lock = asyncio.Lock()

    async def cog_load(self):
        self.process_auto_reminders.start()

    def cog_unload(self):
        self.process_auto_reminders.cancel()
        self.bot.tree.remove_command(
            "Auto Reminder dari Post",
            type=discord.AppCommandType.message,
        )

    @tasks.loop(seconds=30)
    async def process_auto_reminders(self):
        now = datetime.now(timezone.utc)
        due_ids = []
        invalid_ids = []
        for reminder in auto_reminders():
            try:
                reminder_id = reminder["id"]
                next_run = datetime.fromisoformat(reminder["next_run_at"])
                int(reminder["guild_id"])
                int(reminder["channel_id"])
                message = reminder["message"]
                repeat_minutes = reminder.get("repeat_minutes")
                role_id = reminder.get("tag_role_id")
                if role_id is not None:
                    int(role_id)
                if not isinstance(reminder_id, str) or not reminder_id:
                    raise ValueError("ID pengingat tidak valid")
                if (
                    not isinstance(message, str)
                    or not message
                    or len(message) > 2000
                ):
                    raise ValueError("pesan harus berisi 1-2000 karakter")
                if repeat_minutes is not None and not (
                    1 <= int(repeat_minutes) <= 525600
                ):
                    raise ValueError(
                        "interval pengulangan harus 1-525600 menit"
                    )
            except (KeyError, TypeError, ValueError) as exc:
                reminder_id = reminder.get("id")
                print(
                    f"[Auto Reminder] Jadwal {reminder_id or '(tanpa ID)'} "
                    f"tidak valid: {exc}"
                )
                invalid_ids.append(reminder_id)
                continue

            if next_run.tzinfo is None:
                next_run = next_run.replace(tzinfo=timezone.utc)
            if next_run <= now:
                due_ids.append(reminder_id)

        if invalid_ids:
            async with self._reminder_lock:
                data = auto_reminders()
                save_auto_reminders(
                    [
                        reminder for reminder in data
                        if reminder.get("id") not in invalid_ids
                    ]
                )

        for reminder_id in due_ids:
            async with self._reminder_lock:
                data = auto_reminders()
                reminder = next(
                    (
                        item for item in data
                        if item.get("id") == reminder_id
                    ),
                    None,
                )
                if not reminder:
                    continue

                try:
                    guild_id = int(reminder["guild_id"])
                    channel_id = int(reminder["channel_id"])
                    repeat_minutes = reminder.get("repeat_minutes")
                except (KeyError, TypeError, ValueError) as exc:
                    print(
                        f"[Auto Reminder] Konfigurasi {reminder_id} "
                        f"tidak valid: {exc}"
                    )
                    save_auto_reminders(
                        [item for item in data if item.get("id") != reminder_id]
                    )
                    continue

                guild = self.bot.get_guild(guild_id)
                if guild is None:
                    print(
                        f"[Auto Reminder] Server {guild_id} tidak tersedia; "
                        f"jadwal {reminder_id} dicoba kembali dalam 15 menit."
                    )
                    reminder["next_run_at"] = (
                        datetime.now(timezone.utc) + timedelta(minutes=15)
                    ).isoformat()
                    save_auto_reminders(data)
                    continue

                channel = guild.get_channel_or_thread(channel_id)
                if not isinstance(
                    channel,
                    (discord.TextChannel, discord.Thread),
                ):
                    print(
                        f"[Auto Reminder] Channel {channel_id} tidak ditemukan "
                        f"di server {guild_id}; jadwal {reminder_id} dihapus."
                    )
                    save_auto_reminders(
                        [item for item in data if item.get("id") != reminder_id]
                    )
                    continue

                role_id = reminder.get("tag_role_id")
                role = guild.get_role(int(role_id)) if role_id else None
                if role_id and role is None:
                    print(
                        f"[Auto Reminder] Role {role_id} tidak ditemukan "
                        f"di server {guild_id}; reminder dikirim tanpa tag."
                    )
                content = reminder["message"]
                allowed_mentions = discord.AllowedMentions.none()
                if role is not None:
                    content = f"{content}\n{role.mention}"
                    allowed_mentions = discord.AllowedMentions(
                        roles=[role],
                        users=False,
                        everyone=False,
                        replied_user=False,
                    )

                try:
                    await channel.send(
                        content,
                        allowed_mentions=allowed_mentions,
                    )
                except discord.NotFound as exc:
                    print(
                        f"[Auto Reminder] Channel {channel_id} tidak ditemukan "
                        f"saat pengiriman: {exc}; jadwal dihapus."
                    )
                    save_auto_reminders(
                        [item for item in data if item.get("id") != reminder_id]
                    )
                    continue
                except discord.Forbidden as exc:
                    print(
                        f"[Auto Reminder] Tidak dapat mengirim ke channel "
                        f"{channel_id}: {exc}"
                    )
                    reminder["next_run_at"] = (
                        datetime.now(timezone.utc) + timedelta(minutes=15)
                    ).isoformat()
                    save_auto_reminders(data)
                    continue
                except discord.HTTPException as exc:
                    print(
                        f"[Auto Reminder] Pengiriman ke channel "
                        f"{channel_id} gagal: {exc}"
                    )
                    reminder["next_run_at"] = (
                        datetime.now(timezone.utc) + timedelta(minutes=5)
                    ).isoformat()
                    save_auto_reminders(data)
                    continue

                if repeat_minutes is None:
                    save_auto_reminders(
                        [item for item in data if item.get("id") != reminder_id]
                    )
                else:
                    reminder["next_run_at"] = (
                        datetime.now(timezone.utc)
                        + timedelta(minutes=int(repeat_minutes))
                    ).isoformat()
                    save_auto_reminders(data)

    @process_auto_reminders.before_loop
    async def before_process_auto_reminders(self):
        await self.bot.wait_until_ready()

    @app_commands.command(
        name="auto-reminder",
        description="Mengatur pengingat otomatis di channel server.",
    )
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.describe(
        aksi="Tambah, hapus, atau lihat daftar pengingat",
        pesan="Isi pesan pengingat (untuk aksi tambah)",
        jeda_waktu_menit=(
            "Jeda antar-reminder dalam menit; default 1440 (24 jam), berulang selamanya"
        ),
        tag="Role Discord yang di-mention pada setiap reminder (opsional)",
        id_pengingat="ID pengingat yang akan dihapus",
    )
    @app_commands.choices(
        aksi=[
            app_commands.Choice(name="Tambah", value="tambah"),
            app_commands.Choice(name="Hapus", value="hapus"),
            app_commands.Choice(name="Daftar", value="daftar"),
        ]
    )
    async def auto_reminder(
        self,
        interaction: discord.Interaction,
        aksi: app_commands.Choice[str],
        pesan: str | None = None,
        jeda_waktu_menit: app_commands.Range[int, 1, 525600] = (
            AUTO_REMINDER_INTERVAL_MINUTES
        ),
        tag: discord.Role | None = None,
        id_pengingat: str | None = None,
    ):
        if interaction.guild is None:
            return await interaction.response.send_message(
                "Perintah ini hanya dapat digunakan di dalam server.",
                ephemeral=True,
            )

        guild_id = str(interaction.guild.id)
        async with self._reminder_lock:
            data = auto_reminders()
            server_reminders = [
                reminder for reminder in data
                if reminder.get("guild_id") == guild_id
            ]

            if aksi.value == "daftar":
                if not server_reminders:
                    return await interaction.response.send_message(
                        "Belum ada pengingat otomatis di server ini.",
                        ephemeral=True,
                    )

                embed = discord.Embed(
                    title="⏰ Daftar Auto Reminder",
                    color=discord.Color.from_rgb(154, 185, 195),
                )
                for reminder in server_reminders[:25]:
                    try:
                        next_run = datetime.fromisoformat(
                            reminder["next_run_at"]
                        )
                        channel_id = int(reminder["channel_id"])
                    except (KeyError, TypeError, ValueError):
                        continue
                    if next_run.tzinfo is None:
                        next_run = next_run.replace(tzinfo=timezone.utc)

                    interval = reminder.get("repeat_minutes")
                    if interval is not None:
                        cadence = f"Setiap {interval} menit, selamanya"
                    else:
                        cadence = "Sekali kirim"
                    role_id = reminder.get("tag_role_id")
                    tag_text = f"\n**Tag:** <@&{role_id}>" if role_id else ""
                    embed.add_field(
                        name=f"ID `{reminder.get('id', '?')}`",
                        value=(
                            f"**Channel:** <#{channel_id}>\n"
                            f"**Pesan:** {reminder.get('message', '')[:100]}\n"
                            f"**Jadwal:** <t:{int(next_run.timestamp())}:R>\n"
                            f"**Jeda waktu:** {cadence}{tag_text}"
                        ),
                        inline=False,
                    )
                if len(server_reminders) > 25:
                    embed.set_footer(
                        text=f"Menampilkan 25 dari {len(server_reminders)} pengingat."
                    )
                return await interaction.response.send_message(
                    embed=embed,
                    ephemeral=True,
                )

            if aksi.value == "hapus":
                if not id_pengingat:
                    return await interaction.response.send_message(
                        "Isi `id_pengingat` untuk menghapus pengingat.",
                        ephemeral=True,
                    )
                updated = [
                    reminder for reminder in data
                    if not (
                        reminder.get("guild_id") == guild_id
                        and reminder.get("id") == id_pengingat
                    )
                ]
                if len(updated) == len(data):
                    return await interaction.response.send_message(
                        "ID pengingat tidak ditemukan di server ini.",
                        ephemeral=True,
                    )
                save_auto_reminders(updated)
                return await interaction.response.send_message(
                    f"✅ Pengingat `{id_pengingat}` berhasil dihapus.",
                    ephemeral=True,
                )

            channel = interaction.channel
            if not isinstance(
                channel,
                (discord.TextChannel, discord.Thread),
            ):
                return await interaction.response.send_message(
                    "Jalankan command ini di channel teks atau thread yang akan "
                    "menerima pengingat.",
                    ephemeral=True,
                )

            if pesan is None or not pesan.strip():
                return await interaction.response.send_message(
                    "Aksi tambah membutuhkan `pesan` yang tidak kosong.",
                    ephemeral=True,
                )

            if len(pesan) > 2000:
                return await interaction.response.send_message(
                    "Pesan pengingat tidak boleh melebihi 2000 karakter.",
                    ephemeral=True,
                )

            if (
                tag is not None
                and not tag.mentionable
                and not interaction.app_permissions.mention_everyone
            ):
                return await interaction.response.send_message(
                    "Bot tidak dapat mention Role tersebut. Aktifkan opsi "
                    "**Allow anyone to mention this role** atau beri bot izin "
                    "**Mention @everyone, @here, and All Roles**.",
                    ephemeral=True,
                )

            if tag is not None and len(pesan.strip()) + len(tag.mention) + 1 > 2000:
                return await interaction.response.send_message(
                    "Pesan terlalu panjang untuk menambahkan mention Role. "
                    "Pendekkan pesan lalu coba lagi.",
                    ephemeral=True,
                )

            reminder_id = uuid.uuid4().hex[:8]
            reminder = {
                "id": reminder_id,
                "guild_id": guild_id,
                "channel_id": str(channel.id),
                "message": pesan.strip(),
                "created_by": str(interaction.user.id),
                "repeat_minutes": jeda_waktu_menit,
                "tag_role_id": str(tag.id) if tag else None,
                "next_run_at": (
                    datetime.now(timezone.utc)
                    + timedelta(minutes=jeda_waktu_menit)
                ).isoformat(),
            }
            data.append(reminder)
            save_auto_reminders(data)

        await interaction.response.send_message(
            f"✅ Pengingat `{reminder_id}` disiapkan di {channel.mention}. "
            f"Pesan pertama dikirim dalam {jeda_waktu_menit} menit, lalu "
            f"berulang selamanya setiap {jeda_waktu_menit} menit"
            f"{f' dengan tag {tag.mention}' if tag else ''}.",
            ephemeral=True,
        )

    @app_commands.default_permissions(manage_channels=True)
    async def auto_reminder_from_post(
        self,
        interaction: discord.Interaction,
        message: discord.Message,
    ):
        if interaction.guild is None or message.guild is None:
            return await interaction.response.send_message(
                "Menu ini hanya dapat digunakan pada post di dalam server.",
                ephemeral=True,
            )

        if message.guild.id != interaction.guild.id:
            return await interaction.response.send_message(
                "Post harus berasal dari server ini.",
                ephemeral=True,
            )

        if not isinstance(
            message.channel,
            (discord.TextChannel, discord.Thread),
        ):
            return await interaction.response.send_message(
                "Jenis channel post ini tidak mendukung pengingat.",
                ephemeral=True,
            )

        await interaction.response.send_modal(
            AutoReminderPostModal(self, message)
        )

async def setup(bot: commands.Bot):
    cog = AutoReminderCog(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(
        app_commands.ContextMenu(
            name="Auto Reminder dari Post",
            callback=cog.auto_reminder_from_post,
        )
    )
