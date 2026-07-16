import discord
from discord.ext import commands
from discord import app_commands

from shared.bot import StrachyBot
from shared import console, messages
from .view import TriviaView
from .game import TriviaGame

class TriviaCog(commands.Cog):
    def __init__(self, bot: StrachyBot) -> None:
        self.bot = bot

    @app_commands.command(
        name="trivia", description="Try to answer a question by selecting 1 of 4 answers.")
    async def trivia(self, interaction: discord.Interaction):
        try:
            console.log_info(f"/trivia: Command used by user {interaction.user.display_name} ({interaction.user.id})")

            game: TriviaGame = TriviaGame()
            view: TriviaView = TriviaView(game=game)

            embed = discord.Embed(color=discord.Color.green(), title="Trivia", description=game.get_question())

            console.log_info(f"/trivia: User {interaction.user.display_name} ({interaction.user.id}) started a new {game}.")
          
            # CRITICAL: Save the sent message reference to the view so the timeout handler can edit it!
            await interaction.response.send_message(embed=embed, view=view)
            view.message = await interaction.original_response()
        except Exception:
            await messages.handle_error("/trivia", interaction)