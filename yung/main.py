import os, discord
from discord.ext import commands
from dotenv import load_dotenv
from bot.loader import load_extensions
load_dotenv()
intents=discord.Intents.default()
intents.guilds=True
intents.guild_messages=True
intents.message_content=True
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
bot=yung(command_prefix="y!", intents=intents)
@bot.event
async def on_ready():
    print(f"Bot telah Online sebagai {bot.user}")
token=os.getenv("DISCORD_TOKEN")
if not token: raise RuntimeError("DISCORD_TOKEN belum diatur di .env")
bot.run(token)
