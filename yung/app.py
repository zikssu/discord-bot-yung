import os, discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from bot.loader import load_extensions
from bot.owner import owner_interaction_check
load_dotenv()

owner_id = os.getenv("BOT_OWNER_ID")
if not owner_id:
    raise RuntimeError("BOT_OWNER_ID belum diatur di .env")
try:
    BOT_OWNER_ID = int(owner_id)
except ValueError as error:
    raise RuntimeError("BOT_OWNER_ID harus berupa Discord User ID numerik.") from error
if BOT_OWNER_ID <= 0:
    raise RuntimeError("BOT_OWNER_ID harus berupa Discord User ID yang valid.")

intents=discord.Intents.default()
intents.guilds=True
intents.guild_messages=True
intents.message_content=True

class OwnerOnlyCommandTree(app_commands.CommandTree):
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await owner_interaction_check(interaction)

class yung(commands.Bot):
    async def setup_hook(self):
        await load_extensions(self)
        guild_id=os.getenv("DISCORD_GUILD_ID")
        if guild_id:
            guild=discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

# =========================
# BOT PRESENCE (yang terlihat di bawah nama bot)
# =========================
# STATUS koneksi: pilih salah satu dengan mengganti `discord.Status.online`.
# discord.Status.online    = Online (titik hijau)
# discord.Status.idle      = Idle (bulan kuning)
# discord.Status.dnd       = Do Not Disturb (bulatan merah)
# discord.Status.invisible = terlihat offline
BOT_STATUS = discord.Status.do_not_disturb

bot=yung(
    command_prefix="y!",
    intents=intents,
    status=BOT_STATUS,
    owner_id=BOT_OWNER_ID,
    tree_cls=OwnerOnlyCommandTree,
)
@bot.event
async def on_ready():
    print(f"Bot telah Online sebagai {bot.user}")
token=os.getenv("DISCORD_TOKEN")
if not token: raise RuntimeError("DISCORD_TOKEN belum diatur di .env")
bot.run(token)