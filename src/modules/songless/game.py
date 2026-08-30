from enum import Enum

from shared import db_manager, logger, models, types

from .models import ESonglessCategory, SonglessSong
from .repository import create_match, get_daily_song, get_random_song, get_song_by_id, update_match


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
        song: SonglessSong | None = None

        if self._is_daily:
            song = await db_manager.execute(db_func=get_daily_song, category=self._category)
        else:
            song = await db_manager.execute(db_func=get_random_song, category=self._category)

        if not song:
            raise RuntimeError("Could not find any songs in the database.")

        match_id: int | None = await db_manager.execute(
            db_func=create_match,
            player_id=self._player.id,
            category=self._category,
            song_id=song.id,
            is_daily=self._is_daily,
        )

        if not match_id:
            raise RuntimeError("Could not create a database record.")

        self._song = song
        self._match_id = match_id

        logger.debug(f"Created new database record with id {self._match_id}.")

    async def _update_db_record(self) -> None:
        await db_manager.execute(
            db_func=update_match,
            match_id=self._match_id,
            status=self._status,
            guesses_count=len(self._guesses),
            guesses=self._guesses,
        )

        logger.debug(f"Updated database record for game {self._match_id}.")

    async def handle_timeout(self) -> None:
        if self._status != models.EMatchStatus.PENDING:
            return

        logger.info(f"Game {self._match_id} timed out.")
        self._status = models.EMatchStatus.TIMEOUT
        await self._update_db_record()

    async def handle_surrender(self) -> None:
        if self._status != models.EMatchStatus.PENDING:
            return

        logger.info(f"User {self._player} gave up game {self._match_id}.")
        self._status = models.EMatchStatus.SURRENDER
        await self._update_db_record()

    async def _handle_guess_submission(self, song: SonglessSong) -> EGuessCategory:
        self._guesses.append(song.id)
        logger.info(f"User {self._player} guessed song '{song.id}' in game {self._match_id}.")
        guess_category: EGuessCategory = EGuessCategory.INCORRECT

        if song.id == self._song.id:
            logger.info(f"User {self._player} won game {self._match_id}.")
            self._status = models.EMatchStatus.WIN
            guess_category = EGuessCategory.CORRECT
        elif song.artist == self._song.artist:
            guess_category = EGuessCategory.ARTIST
        elif len(self._guesses) == 6:
            logger.info(f"User {self._player} lost game {self._match_id}.")
            self._status = models.EMatchStatus.LOSS

        await self._update_db_record()
        return guess_category

    async def submit_guess(self, song_id: int) -> tuple[SonglessSong, EGuessCategory]:
        song: SonglessSong | None = await db_manager.execute(
            db_func=get_song_by_id, song_id=song_id
        )

        if not song:
            raise RuntimeError(f"Song '{song_id}' not found.")

        return (song, await self._handle_guess_submission(song=song))

    async def submit_random_guess(self) -> tuple[SonglessSong, EGuessCategory]:
        song: SonglessSong | None = await db_manager.execute(
            db_func=get_random_song, category=self._category
        )

        if not song:
            raise RuntimeError("Could not find any songs in the database.")

        logger.info(f" Generated random song '{song.id}' for game {self._match_id}")

        return (song, await self._handle_guess_submission(song=song))
