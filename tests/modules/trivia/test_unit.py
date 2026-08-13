from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock

import discord
import pytest

from modules.trivia.game import TriviaGame
from modules.trivia.models import ETriviaCategory, ETriviaDifficulty
from modules.trivia.response import TriviaResponse
from modules.trivia.ui import TriviaButton, TriviaView
from shared import helpers, models
from tests import mocks


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (ETriviaCategory.ANY, "Any"),
        (ETriviaCategory.GENERAL_KNOWLEDGE, "General Knowledge"),
        (ETriviaCategory.MUSICALS_AND_THEATERS, "Musicals & Theatres"),
        (ETriviaCategory.SCIENCE_AND_NATURE, "Science & Nature"),
        (ETriviaCategory.COMPUTERS, "Computers"),
        (ETriviaDifficulty.HARD, "Hard"),
    ],
)
def test_trivia_enums_convert_to_strings(
    value: ETriviaCategory | ETriviaDifficulty, expected: str
) -> None:
    assert str(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (ETriviaCategory.ANY, 0),
        (ETriviaCategory.GENERAL_KNOWLEDGE, 9),
        (ETriviaCategory.BOOKS, 10),
        (ETriviaCategory.CARTOON_AND_ANIMATION, 32),
    ],
)
def test_trivia_category_int_mapping(value: ETriviaCategory, expected: int) -> None:
    assert int(value) == expected


def test_trivia_response_parses_html_and_normalizes_values() -> None:
    payload = {
        "results": [
            {
                "difficulty": "easy",
                "category": "Entertainment: Video Games",
                "question": "What is &quot;A&quot;?",
                "correct_answer": "The letter A",
                "incorrect_answers": ["B", "C", "&lt;tag&gt;"],
            }
        ]
    }

    response = TriviaResponse.model_validate(payload)
    result = response.results[0]

    assert isinstance(response, TriviaResponse)
    assert result.difficulty == ETriviaDifficulty.EASY
    assert result.category == ETriviaCategory.VIDEO_GAMES
    assert result.question == 'What is "A"?'
    assert result.correct_answer == "The letter A"
    assert result.incorrect_answers == ["B", "C", "<tag>"]


@pytest.mark.asyncio
async def test_fetch_api_builds_expected_url_and_populates_game(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_fetch_api(url: str, model_class: TriviaResponse) -> TriviaResponse:
        assert url == "https://opentdb.com/api.php?amount=1&type=multiple&category=9"
        return TriviaResponse.model_validate(
            {
                "results": [
                    {
                        "difficulty": "medium",
                        "category": "Science: Computers",
                        "question": "Question?",
                        "correct_answer": "Answer",
                        "incorrect_answers": ["Wrong 1", "Wrong 2", "Wrong 3"],
                    }
                ]
            }
        )

    monkeypatch.setattr(target=helpers, name="fetch_api", value=fake_fetch_api)

    game = TriviaGame(player_id=7, category=ETriviaCategory.GENERAL_KNOWLEDGE)
    await game.fetch_api()

    assert game.get_player_id() == 7
    assert game.get_category() == ETriviaCategory.COMPUTERS
    assert game.get_difficulty() == ETriviaDifficulty.MEDIUM
    assert game.get_question() == "Question?"
    assert game.get_correct_answer() == "Answer"
    assert game.get_incorrect_answers() == ["Wrong 1", "Wrong 2", "Wrong 3"]


@pytest.mark.asyncio
async def test_fetch_api_raises_when_api_returns_no_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_fetch_api(_url: str, _model_class: TriviaResponse) -> TriviaResponse:
        return TriviaResponse(results=[])

    monkeypatch.setattr(target=helpers, name="fetch_api", value=fake_fetch_api)

    game = TriviaGame(player_id=1)
    with pytest.raises(Exception, match="No API response received"):
        await game.fetch_api()


def test_trivia_view_initializes_buttons_with_expected_labels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("modules.trivia.ui.random.shuffle", lambda items: items.reverse())

    game = TriviaGame(player_id=5, category=ETriviaCategory.ANY, difficulty=ETriviaDifficulty.ANY)
    game._match_id = 12
    game._question = "What?"
    game._correct_answer = "Correct"
    game._incorrect_answers = ["Wrong A", "Wrong B", "Wrong C"]

    view = TriviaView(game=game, timeout=5.0)

    assert len(view.children) == 4
    labels = [child.label for child in view.children if isinstance(child, TriviaButton)]
    assert labels == ["Wrong C", "Wrong B", "Wrong A", "Correct"]


@pytest.mark.asyncio
async def test_trivia_button_correct_answer_updates_embed_and_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    game = TriviaGame(player_id=5)
    game._match_id = 21
    game._question = "Question"
    game._correct_answer = "Correct"
    game._incorrect_answers = ["Wrong"]

    view = TriviaView(game=game, timeout=5.0)
    button = next(
        child for child in view.children if isinstance(child, TriviaButton) and child._is_correct
    )

    embed = discord.Embed(title="Trivia")
    message = SimpleNamespace(embeds=[embed])

    interaction = mocks.DummyInteraction(user_id=5, username="Tester")
    dummy_response = mocks.DummyResponse()
    interaction.response = cast(Any, dummy_response)
    interaction.message = message

    monkeypatch.setattr("modules.trivia.game.update_match", AsyncMock(return_value=True))

    await button.callback(interaction)

    assert game.get_status() is models.EMatchStatus.WIN
    assert embed.color == discord.Color.green()
    assert button.style == discord.ButtonStyle.green
    assert str(button.emoji) == "✔️"
    assert dummy_response.edit_calls


@pytest.mark.asyncio
async def test_trivia_view_rejects_wrong_user(monkeypatch: pytest.MonkeyPatch) -> None:
    game = TriviaGame(player_id=5)
    game._match_id = 21
    game._correct_answer = "Correct"
    game._incorrect_answers = ["Wrong"]

    view = TriviaView(game=game, timeout=5.0)

    interaction = mocks.DummyInteraction(user_id=99, username="Other")
    dummy_response = mocks.DummyResponse()
    interaction.response = cast(Any, dummy_response)
    interaction.message = SimpleNamespace(embeds=[discord.Embed()])
    update_match_mock = AsyncMock(return_value=True)
    monkeypatch.setattr("modules.trivia.game.update_match", update_match_mock)

    await view.interaction_check(interaction)

    assert dummy_response.send_calls
    assert dummy_response.send_calls[0][1]["ephemeral"] is True
    update_match_mock.assert_not_called()
