from typing import List
import discord
from enum import Enum

from shared import console
from shared.types import Position, EDirection, Vector

class ETicTacToeCell(Enum):
    EMPTY = 0
    PLAYER = 1
    OPPONENT = 2


class TicTacToeGrid():
    _size: int
    _grid: List[ETicTacToeCell]

    def __init__(self, size: int):
        self._size = size
        self._grid = [ETicTacToeCell.EMPTY for _ in range(pow(size, 2))]


    def get_size(self) -> int:
        return self._size


    def get_cell_value(self, pos: Position) -> ETicTacToeCell | None:
        """
            Returns value of cell at position (row, col) or None if position is out of bounds.
        """
        if pos.x < 0 or pos.x >= self._size or pos.y < 0 or pos.y >= self._size:
            return None

        return self._grid[pos.x * self._size + pos.y]


    def set_cell_value(self, pos: Position, value: ETicTacToeCell) -> None:
        """
            Sets value of cell at a valid position (row, col).
        """
        if pos.x < 0 or pos.x >= self._size or pos.y < 0 or pos.y >= self._size:
            return

        self._grid[pos.x * self._size + pos.y] = value


class TicTacToeGame():
    match_id: int
    _player: discord.User
    _opponent: discord.User
    _total_moves: int
    _grid: TicTacToeGrid
    _is_over: bool
    _winner: discord.User | None

    def __init__(self, player: discord.User, opponent: discord.User, grid_size: int) -> None:
        self.match_id = -1
        self._player = player
        self._opponent = opponent
        self._total_moves = 0
        self._grid = TicTacToeGrid(grid_size)
        self._is_over = False
        self._winner = None


    def __str__(self) -> str:
        return (
            f"Tic-Tac-Toe game {self.match_id} for player {self._player.id} against opponent {self._opponent.id} "
            f"(total moves: {self._total_moves}, grid_size: {self._grid.get_size()}, is_over: {self._is_over}, winner: {self._winner})."
        )


    def get_player(self) -> discord.User:
        return self._player


    def get_opponent(self) -> discord.User:
        return self._opponent


    def get_total_moves(self) -> int:
        return self._total_moves


    def get_grid_size(self) -> int:
        return self._grid.get_size()


    def get_winner(self) -> discord.User | None:
        return self._winner


    def is_players_turn(self) -> bool:
        return self._total_moves % 2 == 0


    def has_game_ended(self) -> bool:
        return self._is_over


    def play(self, position: Position) -> bool:
        """
            Perform a move by a player who is currently on turn.

            Returns True if move is valid, False otherwise.
        """

        if self._is_over or self._winner:
            console.log_fail(f"/tic-tac-toe: Invalid move for game {self.match_id} - the game already finished.")
            return False

        old_value: ETicTacToeCell | None = self._grid.get_cell_value(pos=position)

        if not old_value:
            console.log_fail(f"/tic-tac-toe: Invalid move for game {self.match_id} - position {position} out of bounds.")
            return False

        if old_value != ETicTacToeCell.EMPTY:
            console.log_fail(f"/tic-tac-toe: Invalid move for game {self.match_id} - cell at position {position} is occupied ({old_value}).")
            return False

        current_player: discord.User = self._player if self.is_players_turn() else self._opponent
        cell_value: ETicTacToeCell = ETicTacToeCell.PLAYER if self.is_players_turn() else ETicTacToeCell.OPPONENT

        self._grid.set_cell_value(pos=position, value=cell_value)
        self._total_moves += 1
        self._end_game(pos=position, current_player=current_player, control_value=cell_value)

        return True


    def _end_game(self, pos: Position, current_player: discord.User, control_value: ETicTacToeCell) -> None:
        """
            Determines whether the game has ended and assigns a winner.
        """
        assert not self._is_over and not self._winner

        for axis in EDirection.get_axes():
            if self._check_axis(pos=pos, axis=axis, control_value=control_value):
                self._winner = current_player
                self._is_over = True
                return

        # Check for draw
        self._is_over = self._total_moves == pow(self._grid.get_size(), 2)


    def _check_axis(self, pos: Position, axis: Vector, control_value: ETicTacToeCell) -> bool:
        """
            Checks axis for 3 connected cells passing through given position.
        """
        assert control_value != ETicTacToeCell.EMPTY

        for start_offset in range(3):
            connected: bool = True

            for i in range(3):
                # Move in positive direction
                row: int = pos.x + (i - start_offset) * axis.x
                col: int = pos.y + (i - start_offset) * axis.y
                cell_value: ETicTacToeCell | None = self._grid.get_cell_value(Position(row, col))

                if cell_value != control_value:
                    connected = False
                    break

            if connected:
                return True

        return False
