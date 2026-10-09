import asyncio
import re
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from bot.commands.automasi.common import BANNER_URL
from bot.store import read, write

PARTNERSHIP_MANAGER_ROLE_ID = "1556885212640710686"
PARTNERSHIP_PING_ROLE_ID = "1557922621386137600"
INVITE_PATTERN = re.compile(
    r"https?://(?:www\.)?(?:discord\.gg/[A-Za-z0-9-]+|"
    r"discord(?:app)?\.com/invite/[A-Za-z0-9-]+)",
    re.IGNORECASE,
)

TICKET_CATEGORIES = {
    "Help": {
        "emoji": "⚠️",
        "roles": ("1556891921618575380",),
    },
    "Lady Verification": {
        "emoji": "♀️",
        "roles": ("1556885189353799730",),
    },
    "Partnership": {
        "emoji": "🤝🏻",
        "roles": ("1556885212640710686",),
    },
    "User Report": {
        "emoji": "👤",
        "roles": ("1556885145460678706",),
    },
    "Bug Report": {
        "emoji": "🐞",
        "roles": (
            "1556909854172512286",
            "1556885118591836170",
            "1556885072555024424",
            "1556885033791258695",
        ),
    },
}


def ticket_settings():
    return read("ticket_settings.json", [], feature="ticket")


def save_ticket_settings(data):
    write("ticket_settings.json", data, feature="ticket")


def tickets():
    return read("tickets.json", [], feature="ticket")


def save_tickets(data):
    write("tickets.json", data, feature="ticket")


def guild_settings(guild_id: int):
    return next(
        (
            item for item in ticket_settings()
            if item.get("guild_id") == str(guild_id)
        ),
        None,
    )


def build_partnership_embed(data: dict, icon_url: str | None):
    embed = discord.Embed(
        description=data["partnership_text"],
        color=discord.Color.from_rgb(154, 185, 195),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_author(name=data["server_name"])
    if icon_url:
        embed.set_thumbnail(url=icon_url)
    embed.add_field(
        name="Perwakilan",
        value=f"<@{data['representative_id']}>",
        inline=True,
    )
    invite_link = data.get("invite_link", "")
    embed.add_field(
        name="Link Invite",
        value=(
            f"[{data['server_name']}]({invite_link})"
            if invite_link
            else "Tidak disertakan"
        ),
        inline=True,
    )
    return embed


def panel_embed():
    embed = discord.Embed(
        title="☎️ home. Services",
        description=(
            "Panel tiket ini disediakan sebagai jalur komunikasi resmi "
            "antara Member dan tim Staf kami.\n\n"
            "Pilih kategori melalui menu di bawah ini untuk membuat tiket. "
            "Setelah tiket "
            "terbuka, mohon sampaikan keperluan kamu secara detail/singkat "
            "tapi jelas agar tim kami dapat memberikan respons dan solusi "
            "secepat mungkin."
        ),
        color=discord.Color.from_rgb(154, 185, 195),
    )
    embed.set_image(url=BANNER_URL)
    return embed


class TicketCategorySelect(discord.ui.Select):
    def __init__(self, cog):
        self.cog = cog
        super().__init__(
            placeholder="Pilih kategori tiket...",
            min_values=1,
            max_values=1,
            custom_id="ticket:category",
            options=[
                discord.SelectOption(
                    label=name,
                    value=name,
                    emoji=category["emoji"],
                )
                for name, category in TICKET_CATEGORIES.items()
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        if not interaction.message:
            return await interaction.response.send_message(
                "Panel tiket tidak dapat diverifikasi.",
                ephemeral=True,
            )
        category_name = self.values[0]
        if category_name == "Help":
            return await interaction.response.send_modal(
                HelpTicketModal(self.cog, interaction.message.id)
            )
        await self.cog.open_ticket(
            interaction,
            category_name,
            interaction.message.id,
        )


class TicketPanelView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.add_item(TicketCategorySelect(cog))


class HelpTicketModal(discord.ui.Modal):
    reason = discord.ui.TextInput(
        label="Keperluan apa yang penting?",
        style=discord.TextStyle.paragraph,
        placeholder="Jelaskan bantuan yang kamu perlukan...",
        max_length=1500,
        required=True,
    )

    def __init__(self, cog, panel_message_id: int):
        super().__init__(title="Ticket Help")
        self.cog = cog
        self.panel_message_id = panel_message_id

    async def on_submit(self, interaction: discord.Interaction):
        reason = self.reason.value.strip()
        if not reason:
            return await interaction.response.send_message(
                "Keperluan tidak boleh kosong.",
                ephemeral=True,
            )
        await self.cog.open_ticket(
            interaction,
            "Help",
            self.panel_message_id,
            reason=reason,
        )


class PartnershipModal(discord.ui.Modal):
    def __init__(self, cog, ticket_key: str, user_id: int):
        super().__init__(title="Informasi Partnership")
        self.cog = cog
        self.ticket_key = ticket_key
        self.server_name = discord.ui.TextInput(
            label="Nama Server",
            max_length=100,
            required=True,
        )
        self.partnership_text = discord.ui.TextInput(
            label="Teks Partnership",
            style=discord.TextStyle.paragraph,
            max_length=1024,
            required=True,
        )
        self.representative_id = discord.ui.TextInput(
            label="User ID Perwakilan (opsional)",
            placeholder="Otomatis diisi dengan User ID kamu",
            default=str(user_id),
            max_length=20,
            required=False,
        )
        self.invite_link = discord.ui.TextInput(
            label="Link Invite (opsional)",
            placeholder="Otomatis diambil dari Teks Partnership jika ada",
            max_length=200,
            required=False,
        )
        self.add_item(self.server_name)
        self.add_item(self.partnership_text)
        self.add_item(self.representative_id)
        self.add_item(self.invite_link)

    async def on_submit(self, interaction: discord.Interaction):
        server_name = self.server_name.value.strip()
        partnership_text = self.partnership_text.value.strip()
        if not server_name or not partnership_text:
            return await interaction.response.send_message(
                "Nama server dan teks partnership tidak boleh kosong.",
                ephemeral=True,
            )
        representative_id = self.representative_id.value.strip()
        if not representative_id:
            representative_id = str(interaction.user.id)
        if not representative_id.isdecimal():
            return await interaction.response.send_message(
                "User ID perwakilan harus berupa angka.",
                ephemeral=True,
            )
        invite_link = self.invite_link.value.strip()
        if not invite_link:
            match = INVITE_PATTERN.search(self.partnership_text.value)
            invite_link = match.group(0) if match else ""
        if invite_link and not INVITE_PATTERN.fullmatch(invite_link):
            return await interaction.response.send_message(
                "Link Invite harus berupa tautan invite Discord yang valid.",
                ephemeral=True,
            )
        await self.cog.submit_partnership(
            interaction,
            self.ticket_key,
            {
                "server_name": server_name,
                "partnership_text": partnership_text,
                "representative_id": representative_id,
                "invite_link": invite_link,
            },
        )


class TicketActionView(discord.ui.View):
    def __init__(self, cog, ticket_key: str):
        super().__init__(timeout=None)
        self.cog = cog
        self.ticket_key = ticket_key

    @discord.ui.button(
        label="Tutup Ticket",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="ticket:close",
    )
    async def close_ticket_button(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ):
        await self.cog.close_ticket(interaction, self.ticket_key)

    @discord.ui.button(
        label="Hapus",
        emoji="🗑️",
        style=discord.ButtonStyle.secondary,
        custom_id="ticket:delete",
    )
    async def delete_ticket_button(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ):
        await self.cog.delete_ticket(interaction, self.ticket_key)


class PartnershipTicketView(TicketActionView):
    @discord.ui.button(
        label="Masukkan Teks",
        emoji="📝",
        style=discord.ButtonStyle.primary,
        custom_id="ticket:partnership:submit",
    )
    async def submit_partnership_button(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ):
        if not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message(
                "Gunakan tombol ini di dalam server.",
                ephemeral=True,
            )
        await interaction.response.send_modal(
                PartnershipModal(self.cog, self.ticket_key, interaction.user.id)
        )


class PartnershipReviewView(discord.ui.View):
    def __init__(self, cog, ticket_key: str):
        super().__init__(timeout=None)
        self.cog = cog
        self.ticket_key = ticket_key

    @discord.ui.button(
        label="Accept",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="ticket:partnership:accept",
    )
    async def accept(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ):
        await self.cog.review_partnership(interaction, self.ticket_key, True)

    @discord.ui.button(
        label="Tolak",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="ticket:partnership:reject",
    )
    async def reject(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ):
        await self.cog.review_partnership(interaction, self.ticket_key, False)


class SetupPartnershipChannelSelect(discord.ui.ChannelSelect):
    def __init__(
        self,
        cog,
        panel_channel_id: int,
        log_channel_id: int,
    ):
        self.cog = cog
        self.panel_channel_id = panel_channel_id
        self.log_channel_id = log_channel_id
        super().__init__(
            custom_id="ticket:setup:partnership-channel",
            channel_types=[discord.ChannelType.text],
            placeholder="Pilih channel partnership...",
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild or not self.values:
            return await interaction.response.send_message(
                "Pilih channel teks pada server untuk channel partnership.",
                ephemeral=True,
            )

        selected_channel = self.values[0]
        if (
            selected_channel.guild_id != interaction.guild.id
            or selected_channel.type is not discord.ChannelType.text
        ):
            return await interaction.response.send_message(
                "Pilih channel teks dari server ini untuk partnership.",
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True, thinking=True)
        panel_channel = interaction.guild.get_channel(
            self.panel_channel_id
        )
        log_channel = interaction.guild.get_channel(self.log_channel_id)
        partnership_channel = interaction.guild.get_channel(
            selected_channel.id
        )
        if partnership_channel is None:
            try:
                partnership_channel = await interaction.guild.fetch_channel(
                    selected_channel.id
                )
            except discord.NotFound:
                return await interaction.followup.send(
                    "Channel partnership yang dipilih tidak ditemukan.",
                    ephemeral=True,
                )
            except discord.Forbidden as exc:
                print(
                    "[Ticket] Tidak dapat membaca channel partnership "
                    f"{selected_channel.id}: {exc}"
                )
                return await interaction.followup.send(
                    "Bot tidak dapat mengakses channel partnership yang dipilih.",
                    ephemeral=True,
                )
            except discord.HTTPException as exc:
                print(
                    "[Ticket] Discord gagal membaca channel partnership "
                    f"{selected_channel.id}: {exc}"
                )
                return await interaction.followup.send(
                    "Channel partnership gagal diperiksa. Silakan coba kembali.",
                    ephemeral=True,
                )
        if (
            not isinstance(panel_channel, discord.TextChannel)
            or not isinstance(log_channel, discord.TextChannel)
            or not isinstance(partnership_channel, discord.TextChannel)
        ):
            return await interaction.followup.send(
                "Salah satu channel tidak ditemukan atau bukan channel teks.",
                ephemeral=True,
            )

        await self.cog.finish_ticket_setup(
            interaction,
            panel_channel,
            log_channel,
            partnership_channel,
        )


class SetupPartnershipChannelView(discord.ui.View):
    def __init__(
        self,
        cog,
        panel_channel_id: int,
        log_channel_id: int,
    ):
        super().__init__(timeout=300)
        self.add_item(
            SetupPartnershipChannelSelect(
                cog,
                panel_channel_id,
                log_channel_id,
            )
        )


class PartnershipJoinView(discord.ui.View):
    def __init__(self, invite_link: str):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="Join Server",
                emoji="🔗",
                style=discord.ButtonStyle.link,
                url=invite_link,
            )
        )


class TicketCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._ticket_setup_lock = asyncio.Lock()
        self._ticket_open_lock = asyncio.Lock()
        self._ticket_close_lock = asyncio.Lock()
        self._partnership_review_lock = asyncio.Lock()

    async def cog_load(self):
        self.bot.add_view(TicketPanelView(self))

        for item in tickets():
            action_message_id = item.get(
                "action_message_id",
                item.get("close_message_id"),
            )
            if action_message_id:
                view_type = (
                    PartnershipTicketView
                    if item.get("category") == "Partnership"
                    else TicketActionView
                )
                self.bot.add_view(
                    view_type(self, item["ticket_key"]),
                    message_id=int(action_message_id),
                )
            review_message_id = item.get("review_message_id")
            if (
                review_message_id
                and item.get("partnership_status") == "pending"
            ):
                self.bot.add_view(
                    PartnershipReviewView(self, item["ticket_key"]),
                    message_id=int(review_message_id),
                )

    @app_commands.command(
        name="setup-ticket",
        description="Menyiapkan panel tiket, channel log, dan partnership.",
    )
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.describe(
        channel="Channel teks untuk panel dan thread tiket",
        log_channel="Channel khusus untuk log tiket dibuka dan ditutup",
    )
    async def setup_ticket(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        log_channel: discord.TextChannel,
    ):
        if not interaction.guild:
            return await interaction.response.send_message(
                "Command ini hanya dapat digunakan di server.",
                ephemeral=True,
            )

        await interaction.response.send_message(
            "🎫 **Setup panel tiket**\n"
            "Pilih channel untuk pengumuman partnership yang disetujui.",
            view=SetupPartnershipChannelView(
                self,
                channel.id,
                log_channel.id,
            ),
            ephemeral=True,
        )

    async def finish_ticket_setup(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        log_channel: discord.TextChannel,
        partnership_channel: discord.TextChannel,
    ):
        if not interaction.guild:
            return await interaction.followup.send(
                "Command ini hanya dapat digunakan di server.",
                ephemeral=True,
            )

        async with self._ticket_setup_lock:
            settings = ticket_settings()
            previous = next(
                (
                    item for item in settings
                    if item.get("guild_id") == str(interaction.guild.id)
                ),
                None,
            )
            panel_message = None
            if (
                previous
                and previous.get("channel_id") == str(channel.id)
                and previous.get("panel_message_id")
            ):
                try:
                    panel_message = await channel.fetch_message(
                        int(previous["panel_message_id"])
                    )
                except discord.NotFound:
                    panel_message = None
                except discord.HTTPException as exc:
                    print(f"[Ticket] Gagal mengambil panel sebelumnya: {exc}")
                    return await interaction.followup.send(
                        "Panel tiket sebelumnya tidak dapat diperiksa. "
                        "Tidak ada panel baru yang dikirim.",
                        ephemeral=True,
                    )

            try:
                if panel_message:
                    await panel_message.edit(
                        embed=panel_embed(),
                        view=self._panel_view(),
                    )
                else:
                    panel_message = await channel.send(
                        embed=panel_embed(),
                        view=self._panel_view(),
                    )
            except discord.Forbidden:
                return await interaction.followup.send(
                    "Bot tidak memiliki izin mengirim atau mengedit panel "
                    f"di {channel.mention}.",
                    ephemeral=True,
                )
            except discord.HTTPException as exc:
                print(f"[Ticket] Gagal mengirim panel: {exc}")
                return await interaction.followup.send(
                    "Panel tiket gagal dikirim atau diperbarui.",
                    ephemeral=True,
                )

            updated_settings = [
                item for item in settings
                if item.get("guild_id") != str(interaction.guild.id)
            ]
            updated_settings.append({
                "guild_id": str(interaction.guild.id),
                "channel_id": str(channel.id),
                "log_channel_id": str(log_channel.id),
                "partnership_channel_id": str(partnership_channel.id),
                "panel_message_id": str(panel_message.id),
                "next_ticket_number": (
                    previous.get("next_ticket_number", 1)
                    if previous
                    else 1
                ),
            })
            save_ticket_settings(updated_settings)

        await interaction.followup.send(
            f"✅ Panel tiket siap di {channel.mention}\n"
            f"🧾 Ticket log: {log_channel.mention}\n"
            f"🤝🏻 Partnership: {partnership_channel.mention}\n"
            f"{panel_message.jump_url}",
            ephemeral=True,
        )

    def _panel_view(self):
        return TicketPanelView(self)

    async def open_ticket(
        self,
        interaction: discord.Interaction,
        category_name: str,
        panel_message_id: int,
        *,
        reason: str | None = None,
    ):
        guild = interaction.guild
        if not guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message(
                "Ticket hanya dapat dibuat oleh member server.",
                ephemeral=True,
            )

        config = guild_settings(guild.id)
        if (
            not config
            or config.get("panel_message_id") != str(panel_message_id)
        ):
            return await interaction.response.send_message(
                "Panel tiket sudah tidak aktif. Minta staf menjalankan "
                "`/setup-ticket` kembali.",
                ephemeral=True,
            )

        category = TICKET_CATEGORIES.get(category_name)
        if not category:
            return await interaction.response.send_message(
                "Kategori tiket tidak dikenali.",
                ephemeral=True,
            )
        if (
            category_name == "Partnership"
            and not config.get("partnership_channel_id")
        ):
            return await interaction.response.send_message(
                "Channel partnership belum diatur. Minta staf menjalankan "
                "`/setup-ticket` kembali dengan memilih channel partnership.",
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True, thinking=True)

        async with self._ticket_open_lock:
            all_settings = ticket_settings()
            current = next(
                (
                    item for item in all_settings
                    if item.get("guild_id") == str(guild.id)
                ),
                None,
            )
            if (
                not current
                or current.get("panel_message_id") != str(panel_message_id)
            ):
                return await interaction.followup.send(
                    "Konfigurasi panel berubah. Silakan gunakan panel terbaru.",
                    ephemeral=True,
                )

            parent_channel = guild.get_channel(int(current["channel_id"]))
            if not isinstance(parent_channel, discord.TextChannel):
                return await interaction.followup.send(
                    "Channel tiket tidak ditemukan. Minta staf menjalankan "
                    "`/setup-ticket` kembali.",
                    ephemeral=True,
                )

            ticket_number = current.get("next_ticket_number", 1)
            current["next_ticket_number"] = ticket_number + 1
            save_ticket_settings(all_settings)

            username = interaction.user.name.replace(" ", "-")
            category_slug = category_name.replace(" ", "-")
            thread_name = (
                f"{ticket_number:04d}-{category_slug}-{username}"
            )[:100]
            ticket_key = f"{guild.id}-{ticket_number}"
            thread = None
            try:
                thread = await parent_channel.create_thread(
                    name=thread_name,
                    type=discord.ChannelType.private_thread,
                    invitable=False,
                    auto_archive_duration=1440,
                    reason=f"Ticket {ticket_key} dibuka oleh {interaction.user}",
                )
                await thread.add_user(interaction.user)
                invited_staff = {interaction.user.id}
                for role_id in category["roles"]:
                    staff_role = guild.get_role(int(role_id))
                    if not staff_role:
                        continue
                    for staff_member in staff_role.members:
                        if staff_member.id in invited_staff:
                            continue
                        try:
                            await thread.add_user(staff_member)
                            invited_staff.add(staff_member.id)
                        except discord.HTTPException as exc:
                            print(
                                f"[Ticket] Gagal menambahkan staf "
                                f"{staff_member.id} ke thread {thread.id}: {exc}"
                            )
                if not invited_staff:
                    print(
                        f"[Ticket] Tidak ada anggota role staf yang tersedia "
                        f"di cache untuk ticket {ticket_key}."
                    )

                staff_mentions = " ".join(
                    f"<@&{role_id}>" for role_id in category["roles"]
                )
                opened_embed = discord.Embed(
                    title=f"{category['emoji']} {category_name}",
                    description=(
                        (
                            "Isi informasi partnership melalui tombol "
                            "**Masukkan Teks**. Pengajuan akan ditinjau "
                            "Partnership Manager sebelum dipublikasikan."
                        )
                        if category_name == "Partnership"
                        else (
                            f"Halo {interaction.user.mention}, sampaikan "
                            "keperluan kamu secara jelas di thread ini. Staf "
                            "akan merespons secepat mungkin."
                        )
                    ),
                    color=discord.Color.from_rgb(154, 185, 195),
                    timestamp=datetime.now(timezone.utc),
                )
                opened_embed.add_field(
                    name="Ticket Number",
                    value=f"`{ticket_number:04d}`",
                    inline=True,
                )
                opened_embed.add_field(
                    name="Dibuat oleh",
                    value=interaction.user.mention,
                    inline=True,
                )
                if reason:
                    opened_embed.add_field(
                        name="Keperluan",
                        value=reason,
                        inline=False,
                    )
                action_view = (
                    PartnershipTicketView(self, ticket_key)
                    if category_name == "Partnership"
                    else TicketActionView(self, ticket_key)
                )
                opened_message = await thread.send(
                    content=staff_mentions,
                    embed=opened_embed,
                    view=action_view,
                    allowed_mentions=discord.AllowedMentions(
                        users=True,
                        roles=True,
                        everyone=False,
                    ),
                )
            except discord.Forbidden as exc:
                print(f"[Ticket] Izin Discord ditolak saat membuat tiket: {exc}")
                await self._cleanup_failed_thread(thread)
                return await interaction.followup.send(
                    "Ticket gagal dibuat. Pastikan bot memiliki izin "
                    "**Create Private Threads**, **Send Messages in Threads**, "
                    "dan **Manage Threads** pada channel tiket.",
                    ephemeral=True,
                )
            except discord.HTTPException as exc:
                print(f"[Ticket] Discord gagal membuat tiket: {exc}")
                await self._cleanup_failed_thread(thread)
                return await interaction.followup.send(
                    "Discord gagal memproses pembuatan ticket. Silakan coba "
                    "kembali beberapa saat lagi.",
                    ephemeral=True,
                )

            ticket_record = {
                "ticket_key": ticket_key,
                "guild_id": str(guild.id),
                "thread_id": str(thread.id),
                "action_message_id": str(opened_message.id),
                "opener_id": str(interaction.user.id),
                "category": category_name,
                "ticket_number": ticket_number,
                "staff_role_ids": list(category["roles"]),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            if reason:
                ticket_record["reason"] = reason
            current_tickets = tickets()
            current_tickets.append(ticket_record)
            save_tickets(current_tickets)

            self.bot.add_view(
                action_view,
                message_id=opened_message.id,
            )

            logged = await self._log_event(
                guild,
                current,
                "Ticket Dibuka",
                ticket_record,
                interaction.user,
                thread,
            )

        result = f"✅ Ticket kamu dibuat: {thread.mention}"
        if not logged:
            result += "\n⚠️ Ticket log gagal dikirim. Staf perlu memeriksa channel log."
        await interaction.followup.send(result, ephemeral=True)

    async def submit_partnership(
        self,
        interaction: discord.Interaction,
        ticket_key: str,
        partnership: dict,
    ):
        guild = interaction.guild
        thread = interaction.channel
        if not guild or not isinstance(thread, discord.Thread):
            return await interaction.response.send_message(
                "Pengajuan partnership hanya dapat dikirim di dalam ticket.",
                ephemeral=True,
            )

        record = next(
            (
                item for item in tickets()
                if item.get("ticket_key") == ticket_key
                and item.get("thread_id") == str(thread.id)
            ),
            None,
        )
        if not record or record.get("category") != "Partnership":
            return await interaction.response.send_message(
                "Ticket partnership ini sudah tidak aktif.",
                ephemeral=True,
            )
        if str(interaction.user.id) != record.get("opener_id"):
            return await interaction.response.send_message(
                "Hanya pembuat ticket yang dapat mengirim informasi partnership.",
                ephemeral=True,
            )
        if record.get("partnership_status") in ("pending", "approved"):
            return await interaction.response.send_message(
                "Informasi partnership sudah dikirim untuk ditinjau.",
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True, thinking=True)
        invite_icon_url = None
        invite_link = partnership["invite_link"]
        if invite_link:
            try:
                invite = await self.bot.fetch_invite(
                    invite_link,
                    with_counts=False,
                    with_expiration=False,
                )
                guild_asset = getattr(invite.guild, "icon", None)
                if guild_asset:
                    invite_icon_url = guild_asset.url
            except discord.HTTPException as exc:
                print(
                    f"[Ticket] Gagal mengambil logo dari invite "
                    f"{invite_link}: {exc}"
                )

        review_embed = build_partnership_embed(
            partnership,
            invite_icon_url,
        )

        review_view = PartnershipReviewView(self, ticket_key)
        try:
            review_message = await thread.send(
                content=f"<@&{PARTNERSHIP_MANAGER_ROLE_ID}>",
                embed=review_embed,
                view=review_view,
                allowed_mentions=discord.AllowedMentions(
                    roles=True,
                    users=False,
                    everyone=False,
                ),
            )
        except discord.Forbidden as exc:
            print(f"[Ticket] Tidak dapat mengirim pengajuan review: {exc}")
            return await interaction.followup.send(
                "Pengajuan gagal dikirim. Bot tidak memiliki izin mengirim "
                "pesan di thread ticket.",
                ephemeral=True,
            )
        except discord.HTTPException as exc:
            print(f"[Ticket] Discord gagal mengirim pengajuan review: {exc}")
            return await interaction.followup.send(
                "Pengajuan gagal diproses oleh Discord. Silakan coba kembali.",
                ephemeral=True,
            )

        all_tickets = tickets()
        record = next(
            item for item in all_tickets
            if item.get("ticket_key") == ticket_key
        )
        record.update({
            "partnership_status": "pending",
            "partnership_data": partnership,
            "partnership_icon_url": invite_icon_url,
            "review_message_id": str(review_message.id),
        })
        save_tickets(all_tickets)
        self.bot.add_view(
            review_view,
            message_id=review_message.id,
        )
        await interaction.followup.send(
            "✅ Informasi partnership berhasil dikirim untuk ditinjau.",
            ephemeral=True,
        )

    async def review_partnership(
        self,
        interaction: discord.Interaction,
        ticket_key: str,
        accepted: bool,
    ):
        guild = interaction.guild
        member = interaction.user
        if not guild or not isinstance(member, discord.Member):
            return await interaction.response.send_message(
                "Tombol review hanya dapat digunakan oleh member server.",
                ephemeral=True,
            )
        if not any(
            role.id == int(PARTNERSHIP_MANAGER_ROLE_ID)
            for role in member.roles
        ):
            return await interaction.response.send_message(
                "Hanya Partnership Manager yang dapat menyetujui atau menolak "
                "pengajuan ini.",
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True, thinking=True)
        async with self._partnership_review_lock:
            all_tickets = tickets()
            record = next(
                (
                    item for item in all_tickets
                    if item.get("ticket_key") == ticket_key
                ),
                None,
            )
            if not record or record.get("partnership_status") != "pending":
                return await interaction.followup.send(
                    "Pengajuan ini sudah diproses atau tidak lagi tersedia.",
                    ephemeral=True,
                )

            config = guild_settings(guild.id)
            if not config:
                return await interaction.followup.send(
                    "Konfigurasi ticket server tidak ditemukan.",
                    ephemeral=True,
                )

            if accepted:
                destination_id = config.get("partnership_channel_id")
                destination = (
                    guild.get_channel(int(destination_id))
                    if destination_id
                    else None
                )
                partnership = record.get("partnership_data", {})
                if not isinstance(destination, discord.TextChannel):
                    return await interaction.followup.send(
                        "Channel publik partnership tidak ditemukan. Jalankan "
                        "`/setup-ticket` kembali untuk mengaturnya.",
                        ephemeral=True,
                    )
                invite_link = partnership.get("invite_link", "")
                icon_url = record.get("partnership_icon_url")
                announcement = build_partnership_embed(partnership, icon_url)

                try:
                    published = await destination.send(
                        content=f"<@&{PARTNERSHIP_PING_ROLE_ID}>",
                        embed=announcement,
                        view=(
                            PartnershipJoinView(invite_link)
                            if invite_link
                            else None
                        ),
                        allowed_mentions=discord.AllowedMentions(
                            roles=True,
                            users=False,
                            everyone=False,
                        ),
                    )
                except discord.Forbidden as exc:
                    print(f"[Ticket] Tidak dapat mengirim partnership: {exc}")
                    return await interaction.followup.send(
                        "Pengajuan belum disetujui karena bot tidak dapat "
                        "mengirim pesan di channel partnership.",
                        ephemeral=True,
                    )
                except discord.HTTPException as exc:
                    print(f"[Ticket] Discord gagal mengirim partnership: {exc}")
                    return await interaction.followup.send(
                        "Pengajuan belum disetujui karena Discord gagal "
                        "mengirim pengumuman.",
                        ephemeral=True,
                    )
                record["partnership_status"] = "approved"
                record["partnership_message_id"] = str(published.id)
                record["reviewed_by"] = str(member.id)
                record["reviewed_at"] = datetime.now(timezone.utc).isoformat()
                result = (
                    f"✅ Partnership disetujui dan dikirim ke "
                    f"{destination.mention}."
                )
            else:
                record["partnership_status"] = "rejected"
                record["reviewed_by"] = str(member.id)
                record["reviewed_at"] = datetime.now(timezone.utc).isoformat()
                result = "❌ Pengajuan partnership ditolak."

            save_tickets(all_tickets)

            if interaction.message:
                final_embed = (
                    interaction.message.embeds[0].copy()
                    if interaction.message.embeds
                    else discord.Embed(title="Review Partnership")
                )
                final_embed.add_field(
                    name="Status Review",
                    value=(
                        f"{'✅ Disetujui' if accepted else '❌ Ditolak'} "
                        f"oleh {member.mention}"
                    ),
                    inline=False,
                )
                disabled_view = PartnershipReviewView(self, ticket_key)
                for child in disabled_view.children:
                    child.disabled = True
                try:
                    await interaction.message.edit(
                        embed=final_embed,
                        view=disabled_view,
                    )
                except discord.HTTPException as exc:
                    print(
                        f"[Ticket] Gagal memperbarui status review "
                        f"{ticket_key}: {exc}"
                    )
                    result += (
                        "\n⚠️ Status berhasil disimpan, tetapi pesan review "
                        "tidak dapat diperbarui."
                    )

        await interaction.followup.send(result, ephemeral=True)

    async def delete_ticket(self, interaction: discord.Interaction, ticket_key: str):
        guild = interaction.guild
        thread = interaction.channel
        member = interaction.user
        if (
            not guild
            or not isinstance(thread, discord.Thread)
            or not isinstance(member, discord.Member)
        ):
            return await interaction.response.send_message(
                "Tombol hapus hanya dapat digunakan di dalam ticket server.",
                ephemeral=True,
            )

        async with self._ticket_close_lock:
            all_tickets = tickets()
            record = next(
                (
                    item for item in all_tickets
                    if item.get("ticket_key") == ticket_key
                    and item.get("thread_id") == str(thread.id)
                ),
                None,
            )
            if not record:
                return await interaction.response.send_message(
                    "Ticket ini sudah dihapus atau tidak terdaftar.",
                    ephemeral=True,
                )
            if not self._is_assigned_staff(member, record):
                return await interaction.response.send_message(
                    "Hanya staf yang mengurus kategori ticket ini yang dapat "
                    "menghapusnya.",
                    ephemeral=True,
                )

            await interaction.response.defer(ephemeral=True, thinking=True)
            logged = False
            try:
                await thread.delete(reason=f"Ticket dihapus oleh {member}")
            except discord.Forbidden as exc:
                print(f"[Ticket] Tidak dapat menghapus thread {thread.id}: {exc}")
                return await interaction.followup.send(
                    "Bot tidak memiliki izin **Manage Threads** untuk "
                    "menghapus ticket ini.",
                    ephemeral=True,
                )
            except discord.HTTPException as exc:
                print(f"[Ticket] Discord gagal menghapus thread {thread.id}: {exc}")
                return await interaction.followup.send(
                    "Ticket gagal dihapus oleh Discord. Silakan coba kembali.",
                    ephemeral=True,
                )

            config = guild_settings(guild.id)
            if config:
                logged = await self._log_event(
                    guild,
                    config,
                    "Ticket Dihapus",
                    record,
                    member,
                    thread,
                )
            save_tickets(
                [
                    item for item in all_tickets
                    if item.get("ticket_key") != ticket_key
                ]
            )

        result = "🗑️ Ticket berhasil dihapus."
        if not logged:
            result += "\n⚠️ Ticket log gagal dikirim atau channel log belum disiapkan."
        await interaction.followup.send(
            result,
            ephemeral=True,
        )

    @staticmethod
    def _is_assigned_staff(member: discord.Member, record: dict) -> bool:
        role_ids = {
            int(role_id) for role_id in record.get("staff_role_ids", [])
        }
        return any(role.id in role_ids for role in member.roles)

    async def close_ticket(
        self,
        interaction: discord.Interaction,
        ticket_key: str,
    ):
        guild = interaction.guild
        thread = interaction.channel
        if not guild or not isinstance(thread, discord.Thread):
            return await interaction.response.send_message(
                "Tombol ini hanya dapat digunakan di dalam ticket.",
                ephemeral=True,
            )

        async with self._ticket_close_lock:
            current_tickets = tickets()
            record = next(
                (
                    item for item in current_tickets
                    if item.get("ticket_key") == ticket_key
                    and item.get("thread_id") == str(thread.id)
                ),
                None,
            )
            if not record:
                return await interaction.response.send_message(
                    "Ticket ini sudah ditutup atau tidak terdaftar.",
                    ephemeral=True,
                )

            user = interaction.user
            if not isinstance(user, discord.Member):
                return await interaction.response.send_message(
                    "Informasi member server tidak tersedia.",
                    ephemeral=True,
                )
            authorized = (
                str(user.id) == record.get("opener_id")
                or user.guild_permissions.manage_channels
                or any(
                    int(role_id) in {role.id for role in user.roles}
                    for role_id in record.get("staff_role_ids", [])
                )
            )
            if not authorized:
                return await interaction.response.send_message(
                    "Hanya pembuat ticket atau staf terkait yang dapat "
                    "menutup ticket ini.",
                    ephemeral=True,
                )

            await interaction.response.defer(ephemeral=True, thinking=True)
            try:
                await thread.edit(
                    archived=True,
                    locked=True,
                    reason=f"Ticket ditutup oleh {user}",
                )
            except discord.Forbidden as exc:
                print(f"[Ticket] Tidak dapat menutup thread {thread.id}: {exc}")
                return await interaction.followup.send(
                    "Bot tidak memiliki izin **Manage Threads** untuk menutup "
                    "ticket ini.",
                    ephemeral=True,
                )
            except discord.HTTPException as exc:
                print(f"[Ticket] Gagal menutup thread {thread.id}: {exc}")
                return await interaction.followup.send(
                    "Ticket gagal ditutup oleh Discord. Silakan coba kembali.",
                    ephemeral=True,
                )

            config = guild_settings(guild.id)
            logged = bool(
                config
                and await self._log_event(
                    guild,
                    config,
                    "Ticket Ditutup",
                    record,
                    user,
                    thread,
                )
            )
            current_tickets = [
                item for item in current_tickets
                if item.get("ticket_key") != ticket_key
            ]
            save_tickets(current_tickets)

        result = "🔒 Ticket berhasil ditutup."
        if not logged:
            result += "\n⚠️ Ticket log gagal dikirim. Staf perlu memeriksa channel log."
        await interaction.followup.send(result, ephemeral=True)

    async def _cleanup_failed_thread(self, thread: discord.Thread | None):
        if not thread:
            return
        try:
            await thread.delete(reason="Pembersihan ticket yang gagal dibuat")
        except discord.HTTPException as exc:
            print(
                f"[Ticket] Gagal membersihkan thread tiket "
                f"{thread.id}: {exc}"
            )

    async def _log_event(
        self,
        guild: discord.Guild,
        config: dict,
        title: str,
        record: dict,
        actor: discord.abc.User,
        thread: discord.Thread,
    ) -> bool:
        log_channel_id = config.get("log_channel_id")
        log_channel = (
            guild.get_channel(int(log_channel_id))
            if log_channel_id
            else None
        )
        if not isinstance(log_channel, discord.TextChannel):
            print(
                f"[Ticket] Channel log tidak ditemukan untuk server {guild.id}."
            )
            return False

        embed = discord.Embed(
            title=f"🧾 {title}",
            description=f"[Buka thread ticket]({thread.jump_url})",
            color=discord.Color.green() if title == "Ticket Dibuka" else discord.Color.red(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(
            name="Ticket Number",
            value=f"`{record['ticket_number']:04d}`",
            inline=True,
        )
        embed.add_field(name="Kategori", value=record["category"], inline=True)
        embed.add_field(
            name="Pembuat",
            value=f"<@{record['opener_id']}>",
            inline=True,
        )
        embed.add_field(
            name="Diproses oleh",
            value=f"{actor.mention}\n`{actor.id}`",
            inline=False,
        )
        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden as exc:
            print(f"[Ticket] Tidak dapat mengirim log ticket: {exc}")
            return False
        except discord.HTTPException as exc:
            print(f"[Ticket] Discord gagal mengirim log ticket: {exc}")
            return False
        return True


async def setup(bot: commands.Bot):
    await bot.add_cog(TicketCog(bot))
