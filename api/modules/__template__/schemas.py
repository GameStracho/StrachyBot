from pydantic import BaseModel, ConfigDict

from shared.models import EMatchStatus


class StartRequest(BaseModel):
    user_id: int


class UpdateRequest(BaseModel):
    status: EMatchStatus
    moves_count: int = 0


class GameResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_id: int
    status: EMatchStatus
    player_id: int
    moves_count: int = 0
    word: str = ""

    def __str__(self) -> str:
        return (
            f"Game (match_id = {self.match_id}, status = {self.status}, "
            f"player_id = {self.player_id}, moves_count = {self.moves_count}, "
            f"word = {self.word})"
        )
