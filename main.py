import os
import motor.motor_asyncio as motor

import discord
from discord.ext import commands

database_password = os.environ.get("DATABASE_PASSWORD")
db_client = motor.AsyncIOMotorClient(database_password)
db = db_client["kai-kicker"]
user_config = db["user_config"]

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True


class KaiKicker(commands.Bot):
    async def setup_hook(self) -> None:
        initial_extensions = ['cogs.economy', 'cogs.errorhandler', 'cogs.games', 'cogs.help', 'cogs.kai',
                              'cogs.listener', 'cogs.miscellaneous', 'cogs.moderation', 'cogs.modmail']
        for extension in initial_extensions:
            await self.load_extension(extension)


bot = KaiKicker(command_prefix=['k!', 'K!'],
                activity=discord.Activity(type=discord.ActivityType.watching, name="kai get kicked"),
                intents=intents)


@bot.event
async def on_ready():
    print(f'Joined: {bot.user}')


token = os.environ.get("DISCORD_BOT_SECRET")
bot.run(token)
