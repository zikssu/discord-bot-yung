async def load_extensions(bot):
    extensions = [
        "bot.commands.bantuan",
        "bot.commands.utilitas.ping",
        "bot.commands.utilitas.infoserver",
        "bot.commands.utilitas.infouser",
        "bot.commands.automasi.autothread.autothread",
        "bot.commands.automasi.auto_reminder.auto_reminder",
        "bot.commands.automasi.feedback.feedback",
        "bot.commands.automasi.feed.feed",
        "bot.commands.automasi.ticket.ticket",
        "bot.commands.automasi.mic.mic",
        "bot.commands.automasi.moots.moots",
    ]

    for name in extensions:
        print(f"Memuat extension: {name}")
        await bot.load_extension(name)