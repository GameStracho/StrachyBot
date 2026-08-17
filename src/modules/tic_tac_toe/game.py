import random
from enum import Enum

from shared import StrachyBot, logger, models
from shared.types import EDirection, Position, User, Vector

from .repository import create_match, update_match


class ETicTacToeCell(Enum):
    EMPTY = 0
    PLAYER = 1
    OPPONENT = 2


class TicTacToeGrid:
    _size: int
    _grid: list[ETicTacToeCell]

    def __init__(self, size: int):
        self._size = size
        self._grid = [ETicTacToeCell.EMPTY for _ in range(pow(size, 2))]

    @property
    def size(self) -> int:
        return self._size

    def get_cell_value(self, pos: Position) -> ETicTacToeCell | None:
        """
        Returns value of cell at position (row, col) or None if position is out of bounds.
        """
        if pos.x < 0 or pos.x >= self._size or pos.y < 0 or pos.y >= self._size:
            return None

        return self._grid[pos.y * self._size + pos.x]

    def set_cell_value(self, pos: Position, value: ETicTacToeCell) -> None:
        """
        Sets value of cell at a valid position (row, col).
        """
        if pos.x < 0 or pos.x >= self._size or pos.y < 0 or pos.y >= self._size:
            return

        self._grid[pos.y * self._size + pos.x] = value


class TicTacToeGame:
    _bot: StrachyBot | None

    _match_id: int
    _status: models.EMatchStatus
    _player: User
    _opponent: User
    _total_moves: int

    _grid: TicTacToeGrid

    def __init__(self, player: User, opponent: User, grid_size: int) -> None:
        self._bot = None
        self._match_id = -1
        self._status = models.EMatchStatus.PENDING
        self._player = player
        self._opponent = opponent
        self._total_moves = 0
        self._grid = TicTacToeGrid(grid_size)

    def __str__(self) -> str:
        return (
            f"Tic-Tac-Toe game {self._match_id} for player {self._player} "
            f"against opponent {self._opponent} "
            f"(status: {self._status}, total moves: {self._total_moves}, "
            f"grid_size: {self._grid.size})."
        )

    @property
    def match_id(self) -> int:
        return self._match_id

    @property
    def status(self) -> models.EMatchStatus:
        return self._status

    @property
    def player(self) -> User:
        return self._player

    @property
    def opponent(self) -> User:
        return self._opponent

    @property
    def total_moves(self) -> int:
        return self._total_moves

    @property
    def grid_size(self) -> int:
        return self._grid.size

    @property
    def winner(self) -> User | None:
        match self._status:
            case models.EMatchStatus.WIN:
                return self._player
            case models.EMatchStatus.LOSS:
                return self._opponent
            case _:
                return None

    @property
    def target_length(self) -> int:
        """Returns the optimal target line length based on board dimension."""
        if self._grid.size <= 3:
            return 3
        elif self._grid.size in (4, 5):
            return 4
        else:
            return 5

    @property
    def is_players_turn(self) -> bool:
        return self._total_moves % 2 == 0

    async def connect_database(self, bot: StrachyBot) -> None:
        self._bot = bot

        match_id: int | None = await self._bot.execute_db_operation(
            db_func=create_match,
            player_id=self._player.id,
            opponent_id=self._opponent.id,
            grid_size=self._grid.size,
        )

        if match_id:
            self._match_id = match_id
            logger.debug(f"/tic-tac-toe: Created new database record with id {self._match_id}.")

    async def _update_database_record(self) -> None:
        if not self._bot:
            logger.warning(f"/tic-tac-toe: Database is not connected. Skipping update of {self}.")
            return

        await self._bot.execute_db_operation(
            db_func=update_match,
            match_id=self._match_id,
            status=self._status,
            total_moves=self._total_moves,
        )

        logger.debug(f"/tic-tac-toe: Updated database record for game {self._match_id}.")

    async def handle_timeout(self) -> None:
        if self._status != models.EMatchStatus.PENDING:
            return

        logger.info(f"/tic-tac-toe: Game {self._match_id} timed out.")
        self._status = models.EMatchStatus.TIMEOUT
        await self._update_database_record()

    def calculate_bot_move(self) -> Position | None:
        """
        Calculates an intelligent move for the bot opponent.
        Priority 1: Win in 1 move.
        Priority 2: Block opponent's win in 1 move.
        Priority 3: Strategic positional move (center, corners, setup).
        """
        grid_size: int = self._grid.size
        empty_positions: list[Position] = []

        for x in range(grid_size):
            for y in range(grid_size):
                pos = Position(x, y)

                if self._grid.get_cell_value(pos) == ETicTacToeCell.EMPTY:
                    empty_positions.append(pos)

        if not empty_positions:
            return None

        # Priority 1: Check for immediate winning move for the bot
        for pos in empty_positions:
            if self._simulate_win(pos=pos, control_value=ETicTacToeCell.OPPONENT):
                return pos

        # Priority 2: Check for immediate blocking move against human player
        for pos in empty_positions:
            if self._simulate_win(pos=pos, control_value=ETicTacToeCell.PLAYER):
                return pos

        # Priority 3: Strategic positional selection based on score
        best_positions: list[Position] = [empty_positions[0]]
        best_score: int = -1

        for pos in empty_positions:
            score: int = self._score_position(pos=pos)

            if score > best_score:
                best_score = score
                best_positions = [pos]
            elif score == best_score:
                best_positions.append(pos)

        return random.choice(best_positions)

    def _simulate_win(self, pos: Position, control_value: ETicTacToeCell) -> bool:
        assert self._grid.get_cell_value(pos=pos) == ETicTacToeCell.EMPTY

        self._grid.set_cell_value(pos=pos, value=control_value)
        is_win: bool = False

        for axis in EDirection.get_axes():
            if self._check_axis(pos=pos, axis=axis, control_value=control_value):
                is_win = True
                break

        self._grid.set_cell_value(pos=pos, value=ETicTacToeCell.EMPTY)
        return is_win

    def _score_position(self, pos: Position) -> int:
        score: int = 0
        grid_size: int = self._grid.size

        # Center preference
        if grid_size % 2 == 1 and pos.x == grid_size // 2 and pos.y == grid_size // 2:
            score += 4

        # Corner preference
        if pos.x in (0, grid_size - 1) and pos.y in (0, grid_size - 1):
            score += 2

        # Check alignment with existing bot cells (creation of threats)
        for axis in EDirection.get_axes():
            for start_offset in range(self.target_length):
                opponent_count: int = 0
                player_count: int = 0

                for i in range(self.target_length):
                    col: int = pos.x + (i - start_offset) * axis.x
                    row: int = pos.y + (i - start_offset) * axis.y
                    cell: ETicTacToeCell | None = self._grid.get_cell_value(Position(col, row))

                    if cell == ETicTacToeCell.OPPONENT:
                        opponent_count += 1
                    elif cell == ETicTacToeCell.PLAYER:
                        player_count += 1

                if player_count == 0 and opponent_count > 0:
                    score += opponent_count * 2

        return score

    async def play(self, position: Position) -> bool:
        """
        Perform a move by a player who is currently on turn.

        Returns True if move is valid, False otherwise.
        """

        if self._status != models.EMatchStatus.PENDING:
            logger.error(
                f"/tic-tac-toe: Invalid move for game {self._match_id} - the game already finished."
            )
            return False

        old_value: ETicTacToeCell | None = self._grid.get_cell_value(pos=position)

        if not old_value:
            logger.error(
                f"/tic-tac-toe: Invalid move for game {self._match_id} "
                f"- position {position} out of bounds."
            )
            return False

        if old_value != ETicTacToeCell.EMPTY:
            logger.error(
                f"/tic-tac-toe: Invalid move for game {self._match_id} "
                f"- cell at position {position} is occupied ({old_value})."
            )
            return False

        cell_value: ETicTacToeCell = (
            ETicTacToeCell.PLAYER if self.is_players_turn else ETicTacToeCell.OPPONENT
        )

        self._grid.set_cell_value(pos=position, value=cell_value)
        self._total_moves += 1
        self._end_game(pos=position, control_value=cell_value)

        await self._update_database_record()
        return True

    def _end_game(self, pos: Position, control_value: ETicTacToeCell) -> None:
        """
        Determines whether the game has ended and assigns a winner.
        """
        assert self._status is models.EMatchStatus.PENDING

        for axis in EDirection.get_axes():
            if self._check_axis(pos=pos, axis=axis, control_value=control_value):
                self._status = (
                    models.EMatchStatus.WIN
                    if control_value == ETicTacToeCell.PLAYER
                    else models.EMatchStatus.LOSS
                )
                return

        if self._total_moves == pow(self._grid.size, 2):
            self._status = models.EMatchStatus.DRAW

    def _check_axis(self, pos: Position, axis: Vector, control_value: ETicTacToeCell) -> bool:
        """
        Checks axis for connected cells passing through given position.
        """
        assert control_value != ETicTacToeCell.EMPTY

        for start_offset in range(self.target_length):
            connected: bool = True

            for i in range(self.target_length):
                # Move in positive direction
                col: int = pos.x + (i - start_offset) * axis.x
                row: int = pos.y + (i - start_offset) * axis.y
                cell_value: ETicTacToeCell | None = self._grid.get_cell_value(Position(col, row))

                if cell_value != control_value:
                    connected = False
                    break

            if connected:
                return True

        return False
