import discord
from typing import Optional
from discord.ext import commands
from discord import app_commands

from modules.announcement import logic


class AnnouncementCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="announcement", description="Make announcements in chat.")
    async def announcement(
        interaction: discord.Interaction,
        title: Optional[str] = "",
        message:  Optional[str] = "") -> None:
        await logic.announce(interaction, title, message)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AnnouncementCog(bot))
