import discord
from discord.ext import commands
from discord import app_commands

from shared.bot import StrachyBot

class TriviaCog(commands.Cog):
    def __init__(self, bot: StrachyBot) -> None:
        self.bot = bot

    @app_commands.command(
        name="trivia", description="Try to answer a question by selecting 1 of 4 answers.")
    async def trivia(self, interaction: discord.Interaction):
        embed = discord.Embed(
            color=discord.Color.blue(), title="Trivia", description="Question")

        await interaction.response.send_message(embed=embed)
