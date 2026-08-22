import discord
from discord import app_commands
from discord.ext import commands

from shared import db_manager, logger, ui

from .game import WordleGame
from .repository import has_played_daily_challenge
from .ui import WordleView


class WordleCog(commands.Cog):
    @app_commands.command(name="wordle", description="Try to guess a 5-letter word in 6 tries.")
    async def wordle(self, interaction: discord.Interaction, daily_challenge: bool = False) -> None:
        try:
            user = ui.get_user(user=interaction.user)

            logger.debug(f"Command '/wordle' used by user {user}.")

            if daily_challenge and await db_manager.execute(
                db_func=has_played_daily_challenge, player_id=interaction.user.id
            ):
                logger.info(f"User {user} already played today's daily challenge.")

                embed, icon = ui.embed.build_warning(
                    message="You already played today's daily challenge."
                )

                await interaction.response.send_message(embed=embed, file=icon, ephemeral=True)
                return

            game: WordleGame = WordleGame(
                player=ui.get_user(user=interaction.user), is_daily=daily_challenge
            )
            await game.create_db_record()
            view: WordleView = WordleView(game=game, timeout=300.0)
            embed, icon = view.build_embed()

            logger.info(f"New {game} started by user {user}")

            # CRITICAL: Save the sent message to the view so the timeout handler can edit it!
            await interaction.response.send_message(embed=embed, view=view, file=icon)
            view.message = await interaction.original_response()
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)
