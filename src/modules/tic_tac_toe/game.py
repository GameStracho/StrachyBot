import discord

class TicTacToeGame():
    match_id: int
    _player: discord.User
    _opponent: discord.User
    _total_moves: int
    _grid_size: int

    def __init__(self, player: discord.User, opponent: discord.User, grid_size: int) -> None:
        self.match_id = -1
        self._player = player
        self._opponent = opponent
        self._total_moves = 0
        self._grid_size = grid_size


    def __str__(self) -> str:
        return (
            f"Tic-Tac-Toe game {self.match_id} for player {self._player.id} against opponent {self._opponent.id} "
            f"(total moves: {self._total_moves}, grid size: {self._grid_size})"
        )


    def get_player(self) -> discord.User:
        return self._player


    def get_opponent(self) -> discord.User:
        return self._opponent


    def get_total_moves(self) -> int:
        return self._total_moves


    def get_grid_size(self) -> int:
        return self._grid_size

