from enum import Enum

from shared import models, types

from .models import ESonglessCategory, SonglessSong


class EGuessCategory(Enum):
    EMPTY = 0
    INCORRECT = 1
    AUTHOR = 2
    CORRECT = 3

    def __int__(self) -> int:
        return self.value


class Game:
    _match_id: int
    _status: models.EMatchStatus
    _player: types.User
    _category: ESonglessCategory
    _song: SonglessSong
    _is_daily: bool
    _guesses: list[int]

    def __init__(self, player: types.User, category: ESonglessCategory, is_daily: bool) -> None:
        self._match_id = -1
        self._status = models.EMatchStatus.PENDING
        self._player = player
        self._category = category
        self._song = SonglessSong()
        self._is_daily = is_daily
        self._guesses = []

    def __str__(self) -> str:
        return (
            f"SonglessGame (match_id = {self._match_id}, status = {self._status}, "
            f"player = {self._player}, song = {self._song}, "
            f"is_daily = {self._is_daily}, guesses = {self._guesses})"
        )

    @property
    def match_id(self) -> int:
        return self._match_id

    @property
    def status(self) -> models.EMatchStatus:
        return self._status

    @property
    def player(self) -> types.User:
        return self._player

    @property
    def song(self) -> SonglessSong:
        return self._song

    @property
    def song_str(self) -> str:
        return f"{self._song.artist} - {self._song.title}"

    @property
    def is_daily(self) -> bool:
        return self._is_daily

    @property
    def guesses(self) -> list[int]:
        return self._guesses

    async def start(self) -> None:
        pass

    async def _update_db_record(self) -> None:
        pass

    async def handle_timeout(self) -> None:
        self._status = models.EMatchStatus.TIMEOUT

    async def handle_surrender(self) -> None:
        self._status = models.EMatchStatus.SURRENDER

    async def add_guess(self, song: SonglessSong) -> None:
        pass

    async def random_guess(self) -> None:
        pass

    async def categorize_guess(self, song: SonglessSong) -> EGuessCategory:
        return EGuessCategory.EMPTY
