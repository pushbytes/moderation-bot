import discord
from discord.ext import commands
from discord import app_commands
from cogs.ids import *

class SecretCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    secret = app_commands.Group(name="secret", description="Top Secret Commands! Shh!")

    @secret.command(name="acrylic", description="Exclusive.")
    async def acrylic(self, interaction: discord.Interaction, string: str, member: discord.Member = None):
        await interaction.response.send_message("Sending secret message...", ephemeral=True)
        author_roles = [role.id for role in interaction.user.roles]

        # Permission check
        if 1381390158187856086 not in author_roles:
            await interaction.followup.send(f"{X_EMOJI} You don't have permission to use this command.", ephemeral=True)
            return

        # Respond in command channel
        if member:
            try:
                await member.send(string)
            except discord.Forbidden:
                await interaction.followup.send(f"{WARNING_EMOJI} Couldn't DM {member.mention}. They might have DMs disabled.", ephemeral=True)
        else:
            await interaction.channel.send(string)
        await interaction.followup.send(f"{CHECK_EMOJI} Message sent if possible.", ephemeral=True)

