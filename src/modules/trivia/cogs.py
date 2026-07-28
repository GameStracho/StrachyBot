import discord
from discord.ext import commands
from discord import app_commands

from shared import console, messages, bot, helpers, ui
from .ui import TriviaView
from .game import TriviaGame
from .models import ETriviaCategory, ETriviaDifficulty
from .repository import create_match

class TriviaCog(commands.Cog):
    def __init__(self, bot: bot.StrachyBot) -> None:
        self.bot = bot

    @app_commands.command(name="trivia", description="Try to answer a question by selecting 1 of 4 answers.")
    async def trivia(
            self, interaction: discord.Interaction, category: ETriviaCategory = ETriviaCategory.ANY,
            difficulty: ETriviaDifficulty = ETriviaDifficulty.ANY) -> None:
        try:
            # Tells Discord to display "Thinking..." and extends time limit to 15 mins
            await interaction.response.defer()

            console.log_debug(f"/trivia: Command used by user {interaction.user.display_name} ({interaction.user.id})")
            game: TriviaGame = TriviaGame(player_id=interaction.user.id, category=category, difficulty=difficulty)
            await game.fetch_api()

            match_id: int | None = await helpers.execute_db_operation(
                target=self.bot, db_func=create_match,
                player_id=game.get_player_id(), category=game.get_category(), difficulty=game.get_difficulty(),
                question=game.get_question(), correct_answer=game.get_correct_answer()
            )

            if match_id:
                game.match_id = match_id

            view: TriviaView = TriviaView(game=game, timeout=15.0)
            embed = discord.Embed(color=discord.Color.dark_gold())

            embed.add_field(name="Category", value=game.get_category(), inline=True)
            embed.add_field(name="Difficulty", value=game.get_difficulty(), inline=True)
            embed.add_field(name="Question", value=game.get_question(), inline=False)
            embed.add_field(name="Timeout", value=ui.get_timeout_timestamp(view=view), inline=False)

            icon, icon_url = helpers.load_attachment(path=__file__, filename="icon.png")
            embed.set_thumbnail(url=icon_url)

            console.log_info(f"/trivia: User {interaction.user.display_name} ({interaction.user.id}) started a new {game}.")

            # CRITICAL: Save the sent message reference to the view so the timeout handler can edit it!
            await interaction.followup.send(embed=embed, view=view, file=icon)
            view.message = await interaction.original_response()
        except Exception:
            await messages.handle_error(command="/trivia", interaction=interaction, use_followup=True)