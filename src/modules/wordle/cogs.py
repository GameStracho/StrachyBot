import discord
from discord import app_commands
from discord.ext import commands

import console
from shared import StrachyBot, execute_db_operation, ui

from .game import WordleGame
from .repository import has_played_daily_challenge
from .ui import WordleView


class WordleCog(commands.Cog):
    def __init__(self, bot: StrachyBot) -> None:
        self.bot = bot

    @app_commands.command(name="wordle", description="Try to guess a 5-letter word in 6 tries.")
    async def wordle(self, interaction: discord.Interaction, daily_challenge: bool = False) -> None:
        try:
            console.log_debug(
                f"/wordle: Command used by user {interaction.user.display_name} "
                f"({interaction.user.id})"
            )

            if daily_challenge and await execute_db_operation(
                target=self.bot, db_func=has_played_daily_challenge, player_id=interaction.user.id
            ):
                console.log_info(
                    f"/wordle: User {interaction.user.display_name} ({interaction.user.id}) "
                    f"already played the daily challenge."
                )
                await interaction.response.send_message(
                    content="You already played today's daily challenge.", ephemeral=True
                )
                return

            game: WordleGame = WordleGame(player_id=interaction.user.id, is_daily=daily_challenge)
            await game.connect_database(bot=self.bot)
            view: WordleView = WordleView(game=game, timeout=300.0)
            embed, icon = view.build_embed(interaction.user)

            console.log_info(
                f"/wordle: User {interaction.user.display_name} ({interaction.user.id}) "
                f"started a new {game}."
            )

            # CRITICAL: Save the sent message to the view so the timeout handler can edit it!
            await interaction.response.send_message(embed=embed, view=view, file=icon)
            view.message = await interaction.original_response()
        except Exception:
            await ui.handle_error(command="/wordle", interaction=interaction, use_followup=False)
