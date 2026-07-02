import discord
from discord.ext import commands
from discord import app_commands

from modules.utils import logic
from shared.bot import StrachyBot


class UtilsCog(commands.Cog):
    def __init__(self, bot: StrachyBot) -> None:
        self.bot = bot

    @app_commands.command(name="info", description="Show important information about the bot")
    async def info(
        self,
        interaction: discord.Interaction) -> None:
        await logic.show_info(interaction, self.bot.start_time)


async def setup(bot: StrachyBot) -> None:
    await bot.add_cog(UtilsCog(bot))
