import discord
from discord.ext import commands
from discord import app_commands
from cogs.ids import *
from datetime import timedelta
from typing import Optional

class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    mod = app_commands.Group(name="mod", description="Jira Moderation commands")

    def parse_duration(self, duration_str: str) -> Optional[timedelta]:
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

    @mod.command(name="ban", description="Ban a member from the server.")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided", silent: bool = True):
        await interaction.response.send_message("Banning member...", ephemeral=True)
        author_roles = [role.id for role in interaction.user.roles]

        # Check if the user has the authorized role
        if AUTHORIZED_ROLE_ID not in author_roles:
            await interaction.followup.send("❌ You don't have permission to use this command.", ephemeral=True)
            return

        # Prevent banning users with protected roles
        try:
            target_roles = [role.id for role in member.roles]
            if any(role_id in PROTECTED_ROLE_IDS for role_id in target_roles):
                await interaction.followup.send("❌ You cannot ban this user because they have a protected role.", ephemeral=True)
                return
        except:
            pass

        embed = discord.Embed(
            title="🔨 User Banned",
            description=f"**User:** {member.mention}\n**Reason:** {reason}\n**Moderator:** {interaction.user.mention}",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        # Try to DM the user
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            await interaction.followup.send(f"Couldn't DM {member.mention}. They might have DMs disabled.", ephemeral=True)
            #return
        
        # Try banning the user
        try:
            await member.ban(reason=reason)

            await interaction.followup.send(embed=embed, ephemeral=True)

            if silent is False:
                await interaction.followup.send(embed=embed)

            # Send to log channel
            log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(embed=embed)
            else:
                print(f"⚠️ Log channel with ID {LOG_CHANNEL_ID} not found.")

        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to ban this user.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ An unexpected error occurred: {str(e)}", ephemeral=True)

    @mod.command(name="pardon", description="Unban a user from the server.")
    async def pardon(self, interaction: discord.Interaction, user: discord.User, silent: bool = True):
        await interaction.response.send_message("Unbanning member...", ephemeral=True)
        author_roles = [role.id for role in interaction.user.roles]

        # Check if the user has the authorized role
        if AUTHORIZED_ROLE_ID not in author_roles:
            await interaction.followup.send("❌ You don't have permission to use this command.", ephemeral=True)
            return

        try:
            # Check if user is banned
            banned_user = None
            async for ban in interaction.guild.bans():
                if ban.user.id == user.id:
                    banned_user = ban
                    break

            if banned_user is None:
                await interaction.followup.send("⚠️ This user is not banned.", ephemeral=True)
                return

            # Unban the user
            await interaction.guild.unban(user)

            # Create the embed
            embed = discord.Embed(
                title="🕊️ User Unbanned",
                description=f"**User:** {user.mention}\n**Moderator:** {interaction.user.mention}",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
            embed.timestamp = discord.utils.utcnow()

            await interaction.followup.send(embed=embed, ephemeral=True)

            if silent is False:
                await interaction.followup.send(embed=embed)

            # Send embed to log channel
            log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(embed=embed)
            else:
                print(f"⚠️ Log channel with ID {LOG_CHANNEL_ID} not found.")

        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to unban this user.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ An unexpected error occurred: {str(e)}", ephemeral=True)

    @mod.command(name="timeout", description="Temporarily timeout a member.")
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = "No reason provided", silent: bool = True):
        await interaction.response.send_message("Timing member out...", ephemeral=True)
        author_roles = [role.id for role in interaction.user.roles]

        # Permission check
        if AUTHORIZED_ROLE_ID not in author_roles:
            await interaction.followup.send("❌ You don't have permission to use this command.", ephemeral=True)
            return

        # Prevent timing out users with protected roles
        try:
            target_roles = [role.id for role in member.roles]
            if any(role_id in PROTECTED_ROLE_IDS for role_id in target_roles):
                await interaction.followup.send("❌ You cannot timeout this user because they have a protected role.", ephemeral=True)
                return
        except:
            pass

        # Parse the duration string
        timeout_duration = self.parse_duration(duration)
        if not timeout_duration:
            await interaction.followup.send("❌ Invalid duration format. Use something like `10m`, `2h`, `1d`.", ephemeral=True)
            return

        try:
            print(timeout_duration, type(timeout_duration))
            until = discord.utils.utcnow() + timeout_duration
            await member.timeout(until, reason=reason)

            # Create the embed
            embed = discord.Embed(
                title="⏳ User Timed Out",
                description=f"**User:** {member.mention}\n**Duration:** {duration}\n**Reason:** {reason}\n**Moderator:** {interaction.user.mention}",
                color=discord.Color.orange()
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.timestamp = discord.utils.utcnow()

            # Try to DM the user
            try:
                await member.send(embed=embed)
            except discord.Forbidden:
                await interaction.followup.send(f"Couldn't DM {member.mention}. They might have DMs disabled.", ephemeral=True)

            # Respond in command channel
            await interaction.followup.send(embed=embed, ephemeral=True)

            if silent is False:
                await interaction.followup.send(embed=embed)

            # Send to log channel
            log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(embed=embed)
            else:
                print(f"⚠️ Log channel with ID {LOG_CHANNEL_ID} not found.")

        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to timeout this user.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ An unexpected error occurred: {str(e)}", ephemeral=True)

    @mod.command(name="untimeout", description="Remove timeout from a member.")
    async def untimeout(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided", silent: bool = True):
        await interaction.response.send_message("Removing timeout from member...", ephemeral=True)
        author_roles = [role.id for role in interaction.user.roles]

        # Permission check
        if AUTHORIZED_ROLE_ID not in author_roles:
            await interaction.followup.send("❌ You don't have permission to use this command.", ephemeral=True)
            return

        # Prevent timing out users with protected roles
        try:
            target_roles = [role.id for role in member.roles]
            if any(role_id in PROTECTED_ROLE_IDS for role_id in target_roles):
                await interaction.followup.send("❌ You cannot timeout this user because they have a protected role.", ephemeral=True)
                return
        except:
            pass


        try:
            await member.timeout(discord.utils.utcnow() + self.parse_duration('0s'), reason=reason)

            # Create the embed
            embed = discord.Embed(
                title="⏳ User Untimed Out",
                description=f"**User:** {member.mention}\n**Reason:** {reason}\n**Moderator:** {interaction.user.mention}",
                color=discord.Color.orange()
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.timestamp = discord.utils.utcnow()

            # Try to DM the user
            try:
                await member.send(embed=embed)
            except discord.Forbidden:
                await interaction.followup.send(f"Couldn't DM {member.mention}. They might have DMs disabled.", ephemeral=True)

            # Respond in command channel
            await interaction.followup.send(embed=embed, ephemeral=True)

            if silent is False:
                await interaction.followup.send(embed=embed)

            # Send to log channel
            log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(embed=embed)
            else:
                print(f"⚠️ Log channel with ID {LOG_CHANNEL_ID} not found.")

        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to timeout this user.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ An unexpected error occurred: {str(e)}", ephemeral=True)

    @mod.command(name="delete_message", description="Delete a message by its ID.")
    async def delete_message(self, interaction: discord.Interaction, message_id: str, reason: str = "No reason provided", file: discord.Attachment = None, silent: bool = True):
        await interaction.response.send_message("Deleting message...", ephemeral=True)
        author_roles = [role.id for role in interaction.user.roles]

        # Check permission role
        if AUTHORIZED_ROLE_ID not in author_roles:
            await interaction.followup.send("❌ You don't have permission to use this command.", ephemeral=True)
            return

        try:
            # Prevent deletion of protected message IDs
            message_id_int = int(message_id)
            if message_id_int in RESTRICTED_MESSAGE_IDS:
                await interaction.followup.send("🚫 This message is restricted and cannot be deleted.", ephemeral=True)
                return

            # Search all text channels for the message
            target_message = None
            for channel in interaction.guild.text_channels:
                try:
                    msg = await channel.fetch_message(message_id_int)
                    member = msg.author
                    if msg:
                        target_message = msg
                        break
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    continue

            if not target_message:
                await interaction.followup.send("❌ Message not found in any accessible text channel.", ephemeral=True)
                return

            # Check if message author has protected roles
            if isinstance(target_message.author, discord.Member):
                target_roles = [role.id for role in target_message.author.roles]
                if any(rid in PROTECTED_ROLE_IDS for rid in target_roles):
                    await interaction.followup.send("🚫 Cannot delete messages from protected users.", ephemeral=True)
                    return

            await target_message.delete()

            # Create response embed
            embed = discord.Embed(
                title="🗑️ Message Deleted",
                description=f"""
                **Message ID:** `{message_id}`\n
                **Channel:** {target_message.channel.mention}\n
                **Author:** {target_message.author.mention}\n
                **Reason:** {reason}\n
                **Moderator:** {interaction.user.mention}
                """,
                color=discord.Color.red()
            )

            """
            if not file.content_type or not file.content_type.startswith("image/"):
                await interaction.followup.send("Please upload a valid image file (PNG, JPEG, etc.)", ephemeral=True)
                return
            else:
                embed.set_image(url=file.url)
            """

            if file.content_type or file.content_type.startswith("image/"):
                embed.set_image(url=file.url)

            embed.timestamp = discord.utils.utcnow()

            await interaction.followup.send(embed=embed, ephemeral=True)
            
            if silent is False:
                await interaction.followup.send(embed=embed)

            # Send to log channel
            log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(embed=embed)
            else:
                print(f"⚠️ Log channel with ID {LOG_CHANNEL_ID} not found.")

            # Try to DM the user
            try:
                await member.send(embed=embed)
            except discord.Forbidden:
                await interaction.followup.send(f"Couldn't DM {member.mention}. They might have DMs disabled.", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ An unexpected error occurred: {str(e)}", ephemeral=True)



