import discord

from shared import console
import modules.tic_tac_toe.button as button
from .game import TicTacToeGame

class TicTacToeView(discord.ui.View):
    _game: TicTacToeGame

    def __init__(self, game: TicTacToeGame, timeout: float = 15.0):
        super().__init__(timeout=timeout)

        self._game = game

        for row in range(game.get_grid_size()):
            for _col in range(game.get_grid_size()):
                self.add_item(button.TicTacToeButton(game_id=self._game.match_id, row=row))

        console.log_debug((
            f"/tic-tac-toe: New TicTacToeView created for game {self._game.match_id} "
            f"with {timeout}s timeout."
        ))


    def get_game(self) -> TicTacToeGame:
        return self._game
