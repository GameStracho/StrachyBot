import asyncio
import html
import re
from collections import defaultdict, deque
from typing import NamedTuple

from pydantic import BaseModel, field_validator

from shared import helpers, logger, types

from .models import ETriviaCategory, ETriviaDifficulty


class TriviaQuestion(BaseModel):
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
            return re.sub(
                pattern="^(Entertainment|Science): ", repl="", string=html.unescape(value)
            )

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
            f" incorrect answers = {self.incorrect_answers})"
        )


class TriviaAPIResponse(BaseModel):
    results: list[TriviaQuestion]

    def __str__(self) -> str:
        return str(self.results)


class CacheKey(NamedTuple):
    category: ETriviaCategory
    difficulty: ETriviaDifficulty


class TriviaAPIManager:
    """Manages buffered queues of OpenTDB trivia questions to avoid rate limits."""

    _batch_size: int  # up to 50
    _cache: dict[CacheKey, deque[TriviaQuestion]]
    _locks: dict[CacheKey, asyncio.Lock]

    def __init__(self, batch_size: int = 10) -> None:
        self._batch_size = batch_size
        self._cache: dict[CacheKey, deque[TriviaQuestion]] = defaultdict(deque)
        self._locks: dict[CacheKey, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def get_question(
        self, category: ETriviaCategory, difficulty: ETriviaDifficulty
    ) -> TriviaQuestion:
        key = CacheKey(category, difficulty)

        # Use an asyncio Lock so concurrent requests don't trigger duplicate batch fetches
        async with self._locks[key]:
            if not self._cache[key]:
                await self._fetch_batch(category, difficulty)

            return self._cache[key].popleft()

    async def _fetch_batch(self, category: ETriviaCategory, difficulty: ETriviaDifficulty) -> None:
        url = (
            f"https://opentdb.com/api.php?amount={self._batch_size}"
            f"&type=multiple&category={int(category)}"
        )

        if difficulty != ETriviaDifficulty.ANY:
            url = f"{url}&difficulty={str(difficulty).lower()}"

        logger.debug(
            f"Fetching {self._batch_size} question(s) "
            f"for category {category} in difficulty {difficulty} from '{url}'..."
        )

        response: TriviaAPIResponse = await helpers.fetch_api(url, TriviaAPIResponse)

        if not response.results:
            logger.critical(
                f"Failed to fetch API. (category = {category}, difficulty = {difficulty})"
            )
            raise types.NoAPIResponseError()

        key = CacheKey(category, difficulty)
        self._cache[key].extend(response.results)

        logger.debug(
            f"Fetched questions loaded into cache. "
            f"(category = {category}, difficulty = {difficulty})"
        )


# Global manager instance
api_manager = TriviaAPIManager(batch_size=10)
