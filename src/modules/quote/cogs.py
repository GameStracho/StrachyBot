import discord
from discord.ext import commands
from discord import app_commands

from modules.quote import logic


class QuoteCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="quote_guess", description="Try to guess anime by it's quote.")
    async def quote_guess(self, interaction: discord.Interaction):
        await logic.start(interaction)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(QuoteCog(bot))
