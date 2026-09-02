from shared import logger, models

from .models import GameMatch


class Game:
    _id: int
    _status: models.EMatchStatus
    _player_id: int
    _word: str
    _moves_count: int

    def __init__(self, player_id: int, word: str) -> None:
        self._id = -1
        self._status = models.EMatchStatus.PENDING
        self._player_id = player_id
        self._word = word
        self._moves_count = 0

    def __str__(self) -> str:
        return (
            f"Game (match_id = {self._id}, status = {self._status}, "
            f"player_id = {self._player_id}, moves_count = {self._moves_count}, "
            f"word = {self._word})"
        )

    @staticmethod
    def from_db_record(record: GameMatch) -> "Game":
        game = Game(player_id=record.match.player_id, word=record.word)
        game._id = record.match.id
        game._status = record.match.status
        game._moves_count = record.moves_count

        return game

    @property
    def id(self) -> int:
        return self._id

    @property
    def status(self) -> models.EMatchStatus:
        return self._status

    @property
    def player_id(self) -> int:
        return self._player_id

    @property
    def moves_count(self) -> int:
        return self._moves_count

    @property
    def word(self) -> str:
        return self._word

    def submit_move(self) -> None:
        self._moves_count += 1
        logger.info(f"Player {self._player_id} performed move #{self.moves_count}.")
