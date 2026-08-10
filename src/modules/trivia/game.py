from shared import helpers, types

from .models import ETriviaCategory, ETriviaDifficulty
from .response import TriviaResponse


class TriviaGame:
    match_id: int
    _player_id: int
    _question: str
    _incorrect_answers: list[str]
    _correct_answer: str
    _is_over: bool
    _category: ETriviaCategory
    _difficulty: ETriviaDifficulty

    def __init__(
        self,
        player_id: int,
        category: ETriviaCategory = ETriviaCategory.ANY,
        difficulty: ETriviaDifficulty = ETriviaDifficulty.ANY,
    ) -> None:
        self.match_id = -1
        self._player_id = player_id
        self._is_over = False
        self._category = category
        self._difficulty = difficulty

    def __str__(self) -> str:
        return (
            f"Trivia game {self.match_id} for user {self._player_id} - {self._question} "
            f"(difficulty: {self._difficulty}, category: {self._category}, "
            f"is over: {self._is_over}, correct answer: {self._correct_answer}, "
            f"incorrect answers: {self._incorrect_answers})"
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

    def is_over(self) -> bool:
        return self._is_over

    def end(self) -> None:
        self._is_over = True
