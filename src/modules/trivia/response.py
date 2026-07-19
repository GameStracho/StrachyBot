# Classes for parsing response from Open Trivia DB's  API

from pydantic import BaseModel
from typing import List

from .models import ETriviaCategory, ETriviaDifficulty

class TriviaResult(BaseModel):
    difficulty: ETriviaDifficulty
    category: ETriviaCategory
    question: str
    correct_answer: str
    incorrect_answers: List[str]

    def __str__(self) -> str:
        return (
            f"(difficulty = {self.difficulty}, category = {self.category}, "
            f"question = {self.question}, correct_answer = {self.correct_answer}, "
            f" incorrect answers = {self.incorrect_answers})")

class TriviaResponse(BaseModel):
    results: List[TriviaResult]

    def __str__(self) -> str:
        return str(self.results)
