from typing import List
from .models import ETriviaCategory, ETriviaDifficulty

class TriviaGame():
    _game_id: int
    _question: str
    _incorrect_answers: List[str]
    _correct_answer: str
    _is_over: bool
    _category: ETriviaCategory
    _difficulty: ETriviaDifficulty

    def __init__(
            self,
            category: ETriviaCategory = ETriviaCategory.ANY,
            difficulty: ETriviaDifficulty = ETriviaDifficulty.ANY) -> None:
        self._game_id = -1
        self._question = ""
        self._incorrect_answers = []
        self._correct_answer = ""
        self._is_over = False
        self._category = category
        self._difficulty = difficulty

        # TODO: retrieve following info from an API
        for i in range(3):
            self._incorrect_answers.append(f"{i * 2 + 1}")

        self._question = "How many continents are on Earth?"
        self._correct_answer = "7"


    def __str__(self) -> str:
        return (
            f"Trivia game {self._game_id} - {self._question} (difficulty: {self._difficulty}, category: {self._category}, "
            f"is over: {self._is_over}, correct answer: {self._correct_answer}, incorrect answers: {self._incorrect_answers})"
        )

    def get_game_id(self) -> int:
        return self._game_id


    def get_category(self) -> ETriviaCategory:
        return self._category


    def get_difficulty(self) -> ETriviaDifficulty:
        return self._difficulty


    def get_question(self) -> str:
        return self._question


    def get_incorrect_answers(self) -> List[str]:
        return self._incorrect_answers


    def get_correct_answer(self) -> str:
        return self._correct_answer


    def is_over(self) -> bool:
        return self._is_over


    def end(self) -> None:
        self._is_over = True
