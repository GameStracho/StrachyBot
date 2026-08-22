import discord
from discord import app_commands
from discord.ext import commands

from shared import logger, ui

from .game import TriviaGame
from .models import ETriviaCategory, ETriviaDifficulty
from .ui import TriviaView


class TriviaCog(commands.Cog):
    @app_commands.command(
        name="trivia", description="Try to answer a quiz question by selecting 1 of 4 answers."
    )
    async def trivia(
        self,
        interaction: discord.Interaction,
        category: ETriviaCategory = ETriviaCategory.ANY,
        difficulty: ETriviaDifficulty = ETriviaDifficulty.ANY,
    ) -> None:
        try:
            # Tells Discord to display "Thinking..." and extends time limit to 15 mins
            await interaction.response.defer()
            user = ui.get_user(user=interaction.user)

            logger.debug(f"Command '/trivia' used by user {user}.")

            game: TriviaGame = TriviaGame(
                player=ui.get_user(user=interaction.user), category=category, difficulty=difficulty
            )
            await game.fetch_api()
            await game.create_db_record()

            view: TriviaView = TriviaView(game=game, timeout=60.0)
            embed, icon = view.build_embed()

            logger.info(f"New {game} started by user {user}.")

            # CRITICAL: Save the sent message to the view so the timeout handler can edit it!
            await interaction.followup.send(embed=embed, view=view, file=icon)
            view.message = await interaction.original_response()
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)
