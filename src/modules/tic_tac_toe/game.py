from typing import List
import discord
from enum import Enum

from shared import console

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


    def get_cell_value(self, row: int, column: int) -> ETicTacToeCell | None:
        """
            Returns value of cell at position (row, col) or None if position is out of bounds.
        """
        if row < 0 or row >= self._size or column < 0 or column >= self._size:
            return None

        return self._grid[row * self._size + column]


    def set_cell_value(self, row: int, column: int, value: ETicTacToeCell) -> None:
        """
            Sets value of cell at a valid position (row, col).
        """
        if row < 0 or row >= self._size or column < 0 or column >= self._size:
            return

        self._grid[row * self._size + column] = value


    def has_empty_cell(self) -> bool:
        for i in range(len(self._grid)):
            if self._grid[i] == ETicTacToeCell.EMPTY:
                return True
        
        return False


class TicTacToeGame():
    match_id: int
    _player: discord.User
    _opponent: discord.User
    _total_moves: int
    _grid: TicTacToeGrid
    _is_over: bool
    _winner: discord.User | None

    def __init__(self, player_purple: discord.User, player_orange: discord.User, grid_size: int) -> None:
        self.match_id = -1
        self._player = player_purple
        self._opponent = player_orange
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


    def play(self, row: int, column: int) -> bool:
        """
            Perform a move by a player who is currently on turn.

            Returns True if move is valid, False otherwise.
        """

        if self._is_over or self._winner:
            console.log_fail(f"/tic-tac-toe: Invalid move for game {self.match_id} - the game already finished.")
            return False

        old_value: ETicTacToeCell | None = self._grid.get_cell_value(row=row, column=column)

        if not old_value:
            console.log_fail(f"/tic-tac-toe: Invalid move for game {self.match_id} - position ({row, column}) out of bounds.")
            return False

        if old_value != ETicTacToeCell.EMPTY:
            console.log_fail(f"/tic-tac-toe: Invalid move for game {self.match_id} - cell at position ({row, column}) is occupied ({old_value}).")
            return False

        self._grid.set_cell_value(row, column, ETicTacToeCell.PLAYER if self.is_players_turn() else ETicTacToeCell.OPPONENT)
        self._total_moves += 1
        self._end_game(row=row, column=column)

        return True


    def _end_game(self, row: int, column: int) -> None:
        """
            Checks adjacent positions, determines whether the game has ended and assigns a winner.
        """
        assert not self._is_over and not self._winner

        # total_moves is incremented before calling this function, therefore the players must be reversed
        control_value: ETicTacToeCell = ETicTacToeCell.OPPONENT if self.is_players_turn() else ETicTacToeCell.PLAYER

        if (self._check_diagonals(row, column, control_value) or self._check_row(row, column, control_value) 
                or self._check_column(row, column, control_value)):
            self._winner =  self._player if self.is_players_turn() else self._opponent
            self._is_over = True
            return

        self._is_over = self._total_moves == pow(self._grid.get_size(), 2)


    def _check_diagonals(self, row: int, column: int, control_value: ETicTacToeCell) -> bool:
        """
        Checks diagonals for 3 connected cells adjacent to given position.
        Returns True, if 3 cells are connected, False otherwise.
        """
        assert control_value != ETicTacToeCell.EMPTY

        for start_offset in range(3):
            # -- check left diagonal --
            connected_cells: int = 0

            for i in range(1 , 3):
                cell_value: ETicTacToeCell | None = self._grid.get_cell_value(row - start_offset + i, column - start_offset + i)

                if cell_value != control_value:
                    break

                connected_cells += 1

            if connected_cells == 2:
                return True

            # -- check right diagonal --
            connected_cells = 0

            for i in range(1 , 3):
                cell_value = self._grid.get_cell_value(row - start_offset + i, column + start_offset - i)

                if cell_value != control_value:
                    break

                connected_cells += 1

            if connected_cells == 2:
                return True

        return False


    def _check_row(self, row: int, column: int, control_value: ETicTacToeCell) -> bool:
        """
        Checks row for 3 connected cells (control values) adjacent to given position.
        Returns True, if 3 cells are connected, False otherwise.
        """
        assert control_value != ETicTacToeCell.EMPTY

        for start_offset in range(3):
            connected_cells: int = 0

            for i in range(1 , 3):
                cell_value: ETicTacToeCell | None = self._grid.get_cell_value(row, column - start_offset + i)

                if cell_value != control_value:
                    break

                connected_cells += 1

            if connected_cells == 2:
                return True

        return False


    def _check_column(self, row: int, column: int, control_value: ETicTacToeCell) -> bool:
        """
        Checks row for 3 connected cells adjacent to given position.
        Returns True, if 3 cells are connected, False otherwise.
        """
        assert control_value != ETicTacToeCell.EMPTY

        for start_offset in range(3):
            connected_cells: int = 0

            for i in range(1, 3):
                cell_value: ETicTacToeCell | None = self._grid.get_cell_value(row - start_offset + i, column)

                if cell_value != control_value:
                    break

                connected_cells += 1

            if connected_cells == 2:
                return True

        return False
