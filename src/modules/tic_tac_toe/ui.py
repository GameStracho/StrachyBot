import discord

from shared import console, messages
from .game import TicTacToeGame

class TicTacToeView(discord.ui.View):
    _game: TicTacToeGame

    def __init__(self, game: TicTacToeGame, timeout: float = 15.0):
        super().__init__(timeout=timeout)

        self._game = game

        for row in range(game.get_grid_size()):
            for _col in range(game.get_grid_size()):
                self.add_item(TicTacToeButton(game_id=self._game.match_id, row=row))

        console.log_debug((
            f"/tic-tac-toe: New TicTacToeView created for game {self._game.match_id} "
            f"with {timeout}s timeout."
        ))


    def get_game(self) -> TicTacToeGame:
        return self._game


class TicTacToeButton(discord.ui.Button["TicTacToeView"]):
    def __init__(self, game_id: int, row: int) -> None:
        super().__init__(label="⬛", style=discord.ButtonStyle.secondary, row=row)

        console.log_debug((
            f"/tic-tac-toe: New TicTacToeButton created for game {game_id}: "
            f"row = {row}."
        ))

    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            self.label = "⚪"
            self.disabled = True

            parent_view = self.view
            assert isinstance(parent_view, TicTacToeView)

            message: discord.Message | None = interaction.message
            assert message is not None

            embed: discord.Embed = message.embeds[0]

            # hide a second icon appearing above the embed
            embed.set_thumbnail(url="attachment://icon.png")

            # Edit the original message to show disabled buttons
            await interaction.response.edit_message(embed=embed, view=parent_view)
        except Exception:
            await messages.handle_error(command="/tic-tac-toe", interaction=interaction, use_followup=False)
