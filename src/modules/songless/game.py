import io
from enum import Enum

from pydub import AudioSegment

from shared import api, db_manager, logger, models, types

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
    _guesses: list[int | None]

    _preview: AudioSegment

    def __init__(self, player: types.User, category: ESonglessCategory, is_daily: bool) -> None:
        self._match_id = -1
        self._status = models.EMatchStatus.PENDING
        self._player = player
        self._category = category
        self._song = SonglessSong()
        self._is_daily = is_daily
        self._guesses = []
        self._preview = AudioSegment.empty()

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
        return f"{self._song.title} - {self._song.artist}"

    @property
    def category(self) -> ESonglessCategory:
        return self._category

    @property
    def is_daily(self) -> bool:
        return self._is_daily

    @property
    def guesses(self) -> list[int | None]:
        return self._guesses

    @property
    def snippet(self) -> io.BytesIO:
        duration_ms: int = 0

        match len(self._guesses):
            case 0:
                duration_ms = 100
            case 1:
                duration_ms = 500
            case 2:
                duration_ms = 2000
            case 3:
                duration_ms = 4000
            case 4:
                duration_ms = 8000
            case 5:
                duration_ms = 15000
            case _:
                raise ValueError("Exceeded maximum number of guesses.")

        preview_cut: AudioSegment = self._preview[:duration_ms]

        buffer: io.BytesIO = io.BytesIO()
        preview_cut.export(buffer, format="mp3")
        buffer.seek(0)  # Reset stream position to the beginning for reading

        return buffer

    async def start(self) -> None:
        song: SonglessSong | None = None

        if self._is_daily:
            song = await db_manager.execute(db_func=get_daily_song, category=self._category)
        else:
            song = await db_manager.execute(db_func=get_random_song, category=self._category)

        if not song:
            raise RuntimeError("Could not find any songs in the database.")

        fetched_song = await api.fetch_json(url=f"https://api.deezer.com/track/{song.id}/")
        raw_preview = await api.fetch_raw(url=f"{fetched_song['preview']}")
        self._preview = AudioSegment.from_file(io.BytesIO(raw_preview), format="mp3")

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

    async def submit_guess(self, song_id: int) -> tuple[SonglessSong, EGuessCategory]:
        song: SonglessSong | None = await db_manager.execute(
            db_func=get_song_by_id, song_id=song_id
        )

        if not song:
            raise RuntimeError(f"Song '{song_id}' not found.")

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
        return (song, guess_category)

    async def handle_skip(self) -> None:
        self._guesses.append(None)

        logger.info(
            f"User {self._player} skipped turn {len(self._guesses)} of game {self._match_id}."
        )

        if len(self._guesses) == 6:
            logger.info(f"User {self._player} lost game {self._match_id}.")
            self._status = models.EMatchStatus.LOSS

        await self._update_db_record()
