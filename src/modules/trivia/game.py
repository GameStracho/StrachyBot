import console
from shared import StrachyBot, models, types

from .api import TriviaQuestion, api_manager
from .models import ETriviaCategory, ETriviaDifficulty
from .repository import create_match, update_match


class TriviaGame:
    _bot: StrachyBot | None

    _match_id: int
    _status: models.EMatchStatus
    _player: types.User
    _question: str
    _correct_answer: str
    _category: ETriviaCategory
    _difficulty: ETriviaDifficulty

    _incorrect_answers: list[str]

    def __init__(
        self,
        player: types.User,
        category: ETriviaCategory = ETriviaCategory.ANY,
        difficulty: ETriviaDifficulty = ETriviaDifficulty.ANY,
    ) -> None:
        self._bot = None
        self._match_id = -1
        self._status = models.EMatchStatus.PENDING
        self._player = player
        self._is_over = False
        self._category = category
        self._difficulty = difficulty

    def __str__(self) -> str:
        return (
            f"Trivia game {self._match_id} for user {self._player} - {self._question} "
            f"(status: {self._status}, difficulty: {self._difficulty}, category: {self._category}, "
            f"correct answer: {self._correct_answer}, incorrect answers: {self._incorrect_answers})"
        )

    async def fetch_api(self) -> None:
        fetched: TriviaQuestion = await api_manager.get_question(
            category=self._category, difficulty=self._difficulty
        )

        self._category = fetched.category
        self._difficulty = fetched.difficulty
        self._question = fetched.question
        self._correct_answer = fetched.correct_answer
        self._incorrect_answers = fetched.incorrect_answers

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
    def category(self) -> ETriviaCategory:
        return self._category

    @property
    def difficulty(self) -> ETriviaDifficulty:
        return self._difficulty

    @property
    def question(self) -> str:
        return self._question

    @property
    def incorrect_answers(self) -> list[str]:
        return self._incorrect_answers

    @property
    def correct_answer(self) -> str:
        return self._correct_answer

    async def connect_database(self, bot: StrachyBot) -> None:
        self._bot = bot

        match_id: int | None = await self._bot.execute_db_operation(
            db_func=create_match,
            player_id=self._player.id,
            category=self._category,
            difficulty=self._difficulty,
            question=self._question,
            correct_answer=self._correct_answer,
        )

        if match_id:
            self._match_id = match_id
            console.log_debug(f"/trivia: Created new database record with id {self._match_id}.")

    async def _update_database_record(self) -> None:
        if not self._bot:
            console.log_warning(f"/trivia: Database is not connected. Skipping update of {self}.")
            return

        await self._bot.execute_db_operation(
            db_func=update_match, match_id=self._match_id, status=self._status
        )

        console.log_debug(f"/trivia: Updated database record for game {self._match_id}.")

    async def handle_timeout(self) -> None:
        if self._status != models.EMatchStatus.PENDING:
            return

        console.log_info(f"/trivia: Game {self._match_id} timed out.")
        self._status = models.EMatchStatus.TIMEOUT
        await self._update_database_record()

    async def select_answer(self, answer: str) -> bool:
        console.log_debug(
            f"/trivia: User {self._player.id} selected answer '{answer}' for game {self._match_id}"
        )

        if self._status != models.EMatchStatus.PENDING:
            console.log_fail(
                f"/trivia: Game {self._match_id} already finished. Cannot select an answer."
            )
            return False

        is_correct: bool = answer == self._correct_answer

        console.log_info(
            f"/trivia: {'Correct' if is_correct else 'Incorrect'} answer '{answer}' "
            f"chosen for game {self._match_id} by user {self._player.id}."
        )

        self._status = models.EMatchStatus.WIN if is_correct else models.EMatchStatus.LOSS
        await self._update_database_record()

        return True
