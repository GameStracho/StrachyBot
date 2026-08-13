import discord
from discord import app_commands
from discord.ext import commands

import console
from shared import StrachyBot, ui

from .game import TriviaGame
from .models import ETriviaCategory, ETriviaDifficulty
from .ui import TriviaView


class TriviaCog(commands.Cog):
    def __init__(self, bot: StrachyBot) -> None:
        self.bot = bot

    @app_commands.command(
        name="trivia", description="Try to answer a question by selecting 1 of 4 answers."
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

            console.log_debug(
                f"/trivia: Command used by user {interaction.user.display_name} "
                f"({interaction.user.id})"
            )
            game: TriviaGame = TriviaGame(
                player=ui.get_user(user=interaction.user), category=category, difficulty=difficulty
            )
            await game.fetch_api()
            await game.connect_database(self.bot)

            view: TriviaView = TriviaView(game=game, timeout=60.0)
            embed, icon = view.build_embed()

            console.log_info(
                f"/trivia: User {interaction.user.display_name} ({interaction.user.id}) "
                f"started a new {game}."
            )

            # CRITICAL: Save the sent message to the view so the timeout handler can edit it!
            await interaction.followup.send(embed=embed, view=view, file=icon)
            view.message = await interaction.original_response()
        except Exception:
            await ui.handle_error(command="/trivia", interaction=interaction, use_followup=True)
