from typing import Optional

from modules.utils import logic
from shared.bot import StrachyBot

import discord
from discord.ext import commands
from discord import app_commands


class UtilsCog(commands.Cog):
    def __init__(self, bot: StrachyBot) -> None:
        self.bot = bot

    @app_commands.command(name="info", description="Show important information about the bot")
    async def info(
        self,
        interaction: discord.Interaction) -> None:
        await logic.show_info(interaction, self.bot.start_time)


    @app_commands.command(name="announcement", description="Make announcements in chat.")
    async def announcement(
        self,
        interaction: discord.Interaction,
        title: Optional[str] = "",
        message:  Optional[str] = "") -> None:
        await logic.announce(interaction, title, message)


async def setup(bot: StrachyBot) -> None:
    await bot.add_cog(UtilsCog(bot))
