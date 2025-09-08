# Yes i have the same functions in three different files, i have no clue how cogs work xyno lol

import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
from datetime import timedelta, datetime, timezone
from typing import Optional
import json

from cogs import moderation, tools, secret

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

def load_strikes():
        with open(os.path.abspath('strikes.json'), "r") as f:
            return json.load(f)

def save_strikes(data):
    with open(os.path.abspath('strikes.json'), "w") as f:
        json.dump(data, f, indent=4)

def clean_expired_strikes(data):
    now = datetime.now(timezone.utc)
    updated = False
    for guild_id in list(data.keys()):
        for user_id in list(data[guild_id].keys()):
            original_len = len(data[guild_id][user_id])

            data[guild_id][user_id] = [
                strike for strike in data[guild_id][user_id]
                if datetime.fromisoformat(strike["timestamp"]) > now - timedelta(days=30)
            ]

            if not data[guild_id][user_id]:
                del data[guild_id][user_id]
                updated = True
            elif len(data[guild_id][user_id]) != original_len:
                updated = True

        if not data[guild_id]:
            del data[guild_id]
            updated = True

        return updated

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

@tasks.loop(hours=6)
async def auto_clean_strikes():
    data = load_strikes()
    if clean_expired_strikes(data):
        save_strikes(data)

@bot.event
async def on_ready():
    auto_clean_strikes.start()
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()
    print("Commands synced!")

@bot.event
async def on_message(message):
    mention = f'<@{bot.user.id}>'
    if mention in message.content:
        await message.reply("hi my name jira")

token = os.getenv("bot_token")
bot.run(token)
