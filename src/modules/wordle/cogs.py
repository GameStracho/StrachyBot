import discord
from discord.ext import commands
from discord import app_commands

from modules.wordle import logic
from shared.bot import StrachyBot

class WordleCog(commands.Cog):
    def __init__(self, bot: StrachyBot) -> None:
        self.bot = bot

    @app_commands.command(
        name="wordle_play", description="Try to guess a word in 6 tries.")
    async def wordle_play(self, interaction: discord.Interaction):
        await logic.start(interaction)

    @app_commands.command(name="wordle_guess", description="Guess a word in Wordle.")
    async def wordle_guess(self, interaction: discord.Interaction, word: str):
        if logic.is_playing(interaction.user.id):
            await logic.guess(word, interaction)
        else:
            await interaction.response.send_message(
                ephemeral=True, content="You have to start a new game first.")
