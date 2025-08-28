#https://discord.com/api/oauth2/authorize?client_id=1396161419434655855&permissions=8&scope=bot%20applications.commands

import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
from datetime import timedelta, datetime, timezone
from typing import Optional

from cogs import moderation, tools, secret

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

def parse_duration(duration_str: str) -> Optional[timedelta]:
    """Parses duration strings like '10m', '2h', '1d' into timedelta."""
    try:
        unit = duration_str[-1]
        value = int(duration_str[:-1])
        if unit == "s":
            return timedelta(seconds=value)
        elif unit == "m":
            return timedelta(minutes=value)
        elif unit == "h":
            return timedelta(hours=value)
        elif unit == "d":
            return timedelta(days=value)
        else:
            return None
    except:
        return None

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.add_cog(moderation.ModerationCog(self))
        await self.add_cog(tools.ToolsCog(self))
        await self.add_cog(secret.SecretCog(self))

bot = Bot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()
    print("Commands synced!")

token = os.getenv("bot_token")
bot.run(token)
