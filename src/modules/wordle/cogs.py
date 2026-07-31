import discord
from discord import app_commands
from discord.ext import commands

from modules.wordle import logic
from shared import bot, console, messages

from .game import WordleGame


class WordleCog(commands.Cog):
    def __init__(self, bot: bot.StrachyBot) -> None:
        self.bot = bot

    @app_commands.command(
        name="wordle_play", description="Try to guess a word in 6 tries.")
    async def wordle_play(self, interaction: discord.Interaction) -> None:
        await logic.start(interaction)

    @app_commands.command(name="wordle_guess", description="Guess a word in Wordle.")
    async def wordle_guess(self, interaction: discord.Interaction, word: str) -> None:
        if logic.is_playing(interaction.user.id):
            await logic.guess(word, interaction)
        else:
            await interaction.response.send_message(
                ephemeral=True, content="You have to start a new game first.")

    @app_commands.command(name="wordle", description="Try to guess a word in 6 tries.")
    async def wordle(self, interaction: discord.Interaction) -> None:
        try:
            console.log_debug(f"/wordle: Command used by user {interaction.user.display_name} ({interaction.user.id})")

            _game: WordleGame = WordleGame(player_id=interaction.user.id)

        except Exception:
            await messages.handle_error(command="/wordle", interaction=interaction, use_followup=False)