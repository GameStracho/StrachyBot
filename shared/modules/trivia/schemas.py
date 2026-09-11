from pydantic import BaseModel, ConfigDict

from shared.models import EMatchStatus

from .models import ETriviaCategory, ETriviaDifficulty


class StartRequest(BaseModel):
    user_id: int
    category: ETriviaCategory = ETriviaCategory.ANY
    difficulty: ETriviaDifficulty = ETriviaDifficulty.ANY


class TriviaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_id: int
    status: EMatchStatus
    player_id: int
    category: ETriviaCategory
    difficulty: ETriviaDifficulty
    question: str
    correct_answer: str
    incorrect_answers: list[str]

    def __str__(self) -> str:
        return (
            f"Trivia (match_id = {self.match_id}, status = {self.status}, "
            f"player_id = {self.player_id}, category = {self.category}, "
            f"difficulty = {self.difficulty}, question = {self.question})"
        )
