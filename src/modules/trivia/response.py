# Classes for parsing response from Open Trivia DB's  API

import html
import re

from pydantic import BaseModel, field_validator

from .models import ETriviaCategory, ETriviaDifficulty


class TriviaResult(BaseModel):
    difficulty: ETriviaDifficulty
    category: ETriviaCategory
    question: str
    correct_answer: str
    incorrect_answers: list[str]

    # Validate and decode single string fields automatically
    @field_validator("question", "correct_answer", mode="before")
    @classmethod
    def decode_html_entities(cls, value: str) -> str:
        if isinstance(value, str):
            return html.unescape(value)

        return value

    # Validate and decode difficulty field automatically
    @field_validator("difficulty", mode="before")
    @classmethod
    def decode_difficulty(cls, value: str) -> str:
        if isinstance(value, str):
            return value.capitalize()

        return value

    # Validate and decode category field automatically
    @field_validator("category", mode="before")
    @classmethod
    def decode_category(cls, value: str) -> str:
        if isinstance(value, str):
            return re.sub(pattern="^(Entertainment|Science): ", repl="", string=html.unescape(value))

        return value

    # Validate and decode items inside lists (like incorrect answers)
    @field_validator("incorrect_answers", mode="before")
    @classmethod
    def decode_html_list(cls, value: list[str]) -> list[str]:
        if isinstance(value, list):
            return [html.unescape(item) if isinstance(item, str) else item for item in value]

        return value

    def __str__(self) -> str:
        return (
            f"(difficulty = {self.difficulty}, category = {self.category}, "
            f"question = {self.question}, correct_answer = {self.correct_answer}, "
            f" incorrect answers = {self.incorrect_answers})")

class TriviaResponse(BaseModel):
    results: list[TriviaResult]

    def __str__(self) -> str:
        return str(self.results)
