import console
from shared import StrachyBot, execute_db_operation, helpers, models, types

from .models import ETriviaCategory, ETriviaDifficulty
from .repository import create_match, update_match
from .response import TriviaResponse


class TriviaGame:
    _bot: StrachyBot | None

    _match_id: int
    _status: models.EMatchStatus
    _player_id: int
    _question: str
    _correct_answer: str
    _category: ETriviaCategory
    _difficulty: ETriviaDifficulty

    _incorrect_answers: list[str]

    def __init__(
        self,
        player_id: int,
        category: ETriviaCategory = ETriviaCategory.ANY,
        difficulty: ETriviaDifficulty = ETriviaDifficulty.ANY,
    ) -> None:
        self._bot = None
        self._match_id = -1
        self._status = models.EMatchStatus.PENDING
        self._player_id = player_id
        self._is_over = False
        self._category = category
        self._difficulty = difficulty

    def __str__(self) -> str:
        return (
            f"Trivia game {self._match_id} for user {self._player_id} - {self._question} "
            f"(status: {self._status}, difficulty: {self._difficulty}, category: {self._category}, "
            f"correct answer: {self._correct_answer}, incorrect answers: {self._incorrect_answers})"
        )

    async def fetch_api(self) -> None:
        url: str = (
            f"https://opentdb.com/api.php?amount=1&type=multiple&category={int(self._category)}"
        )

        if self._difficulty != ETriviaDifficulty.ANY:
            url = f"{url}&difficulty={str(self._difficulty).lower()}"

        response: TriviaResponse = await helpers.fetch_api(url, TriviaResponse)

        if not len(response.results):
            raise types.NoAPIResponseError()

        self._category = response.results[0].category
        self._difficulty = response.results[0].difficulty
        self._question = response.results[0].question
        self._correct_answer = response.results[0].correct_answer
        self._incorrect_answers = response.results[0].incorrect_answers

    def get_match_id(self) -> int:
        return self._match_id

    def get_status(self) -> models.EMatchStatus:
        return self._status

    def get_player_id(self) -> int:
        return self._player_id

    def get_category(self) -> ETriviaCategory:
        return self._category

    def get_difficulty(self) -> ETriviaDifficulty:
        return self._difficulty

    def get_question(self) -> str:
        return self._question

    def get_incorrect_answers(self) -> list[str]:
        return self._incorrect_answers

    def get_correct_answer(self) -> str:
        return self._correct_answer

    async def connect_database(self, bot: StrachyBot) -> None:
        self._bot = bot

        match_id: int | None = await execute_db_operation(
            target=self._bot,
            db_func=create_match,
            player_id=self._player_id,
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

        await execute_db_operation(
            target=self._bot, db_func=update_match, match_id=self._match_id, status=self._status
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
            f"/trivia: User {self._player_id} selected answer '{answer}' for game {self._match_id}"
        )

        if self._status != models.EMatchStatus.PENDING:
            console.log_fail(
                f"/trivia: Game {self._match_id} already finished. Cannot select an answer."
            )
            return False

        is_correct: bool = answer == self._correct_answer

        console.log_info(
            f"/trivia: {'Correct' if is_correct else 'Incorrect'} answer '{answer}' "
            f"chosen for game {self._match_id} by user {self._player_id}."
        )

        self._status = models.EMatchStatus.WIN if is_correct else models.EMatchStatus.LOSS
        await self._update_database_record()

        return True
