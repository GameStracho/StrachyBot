from enum import Enum

from shared import db_manager, models, types

from .models import ESonglessCategory, SonglessSong
from .repository import create_match, get_song_by_id


class EGuessCategory(Enum):
    EMPTY = 0
    INCORRECT = 1
    ARTIST = 2
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
        match_id: int | None = await db_manager.execute(
            db_func=create_match,
            player_id=self._player.id,
            category=self._category,
            song_id=self._song.id,
            is_daily=self._is_daily,
        )

        if match_id:
            self._match_id = match_id

    async def _update_db_record(self) -> None:
        pass

    async def handle_timeout(self) -> None:
        self._status = models.EMatchStatus.TIMEOUT

    async def handle_surrender(self) -> None:
        self._status = models.EMatchStatus.SURRENDER

    async def submit_guess(self, song_id: int) -> tuple[SonglessSong, EGuessCategory]:
        song: SonglessSong | None = await db_manager.execute(
            db_func=get_song_by_id, song_id=song_id
        )

        if not song:
            raise RuntimeError(f"Song '{song_id}' not found.")

        self._guesses.append(song_id)

        if song.id == self._song.id:
            return (song, EGuessCategory.CORRECT)
        elif song.artist == self._song.artist:
            return (song, EGuessCategory.ARTIST)
        else:
            return (song, EGuessCategory.INCORRECT)

    async def random_guess(self) -> None:
        pass
