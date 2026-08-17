import discord
from discord import app_commands
from discord.ext import commands

from shared import StrachyBot, logger, ui

from .game import TicTacToeGame
from .ui import TicTacToeView


class TicCog(commands.Cog):
    _bot: StrachyBot

    def __init__(self, bot: StrachyBot) -> None:
        self._bot = bot

    @app_commands.command(
        name="tic-tac-toe", description="Challenge someone in a 1v1 Tic-Tac-Toe match"
    )
    @app_commands.choices(
        grid_size=[
            discord.app_commands.Choice(name="3x3", value=3),
            discord.app_commands.Choice(name="4x4", value=4),
            discord.app_commands.Choice(name="5x5", value=5),
        ]
    )
    async def tic_tac_toe(
        self,
        interaction: discord.Interaction,
        opponent: discord.User,
        grid_size: app_commands.Choice[int],
    ) -> None:
        try:
            logger.debug(
                f"Command `/tic-tac-toe` used by user {interaction.user.display_name} "
                f"({interaction.user.id})"
            )

            if opponent.id == interaction.user.id:
                logger.debug("Player and opponent have the same id. Game start abandoned.")

                embed, icon = ui.embed.build_warning(
                    message=(
                        "You cannot play against yourself!\n"
                        "Select a bot as your opponent if you want to play singleplayer. "
                    )
                )

                await interaction.response.send_message(
                    embed=embed,
                    file=icon,
                    ephemeral=True,
                )
                return

            player_emoji, opponent_emoji = ui.get_player_emojis()
            game: TicTacToeGame = TicTacToeGame(
                player=ui.get_user(user=interaction.user, emoji=player_emoji),
                opponent=ui.get_user(user=opponent, emoji=opponent_emoji),
                grid_size=grid_size.value,
            )
            await game.create_db_record()

            view: TicTacToeView = TicTacToeView(game=game, timeout=60.0)
            embed, icon = view.build_embed()

            logger.info(
                f"New game started by user {interaction.user.display_name} ({interaction.user.id})."
            )
            # CRITICAL: Save the sent message to the view so the timeout handler can edit it!
            await interaction.response.send_message(embed=embed, view=view, file=icon)
            view.message = await interaction.original_response()
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)
