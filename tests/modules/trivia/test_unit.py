from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock

import discord
import pytest

from modules.trivia.api import TriviaAPIResponse
from modules.trivia.game import TriviaGame
from modules.trivia.models import ETriviaCategory, ETriviaDifficulty
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

    response = TriviaAPIResponse.model_validate(payload)
    result = response.results[0]

    assert isinstance(response, TriviaAPIResponse)
    assert result.difficulty == ETriviaDifficulty.EASY
    assert result.category == ETriviaCategory.VIDEO_GAMES
    assert result.question == 'What is "A"?'
    assert result.correct_answer == "The letter A"
    assert result.incorrect_answers == ["B", "C", "<tag>"]


@pytest.mark.asyncio
async def test_fetch_api_builds_expected_url_and_populates_game(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_fetch_api(url: str, model_class: TriviaAPIResponse) -> TriviaAPIResponse:
        assert url == "https://opentdb.com/api.php?amount=10&type=multiple&category=9"
        return TriviaAPIResponse.model_validate(
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

    player = mocks.DummyUser(user_id=7)

    game = TriviaGame(player=player, category=ETriviaCategory.GENERAL_KNOWLEDGE)
    await game.fetch_api()

    assert game.player == player
    assert game.category == ETriviaCategory.COMPUTERS
    assert game.difficulty == ETriviaDifficulty.MEDIUM
    assert game.question == "Question?"
    assert game.correct_answer == "Answer"
    assert game.incorrect_answers == ["Wrong 1", "Wrong 2", "Wrong 3"]


@pytest.mark.asyncio
async def test_fetch_api_raises_when_api_returns_no_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_fetch_api(_url: str, _model_class: TriviaAPIResponse) -> TriviaAPIResponse:
        return TriviaAPIResponse(results=[])

    monkeypatch.setattr(target=helpers, name="fetch_api", value=fake_fetch_api)

    game = TriviaGame(player=mocks.DummyUser())
    with pytest.raises(Exception, match="No API response received"):
        await game.fetch_api()


def test_trivia_view_initializes_buttons_with_expected_labels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("modules.trivia.ui.random.shuffle", lambda items: items.reverse())

    game = TriviaGame(
        player=mocks.DummyUser(user_id=5),
        category=ETriviaCategory.ANY,
        difficulty=ETriviaDifficulty.ANY,
    )
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
    user = mocks.DummyUser(user_id=5)
    game = TriviaGame(player=user)
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

    interaction = mocks.DummyInteraction(user=user)
    dummy_response = mocks.DummyResponse()
    interaction.response = cast(Any, dummy_response)
    interaction.message = message

    monkeypatch.setattr("modules.trivia.game.update_match", AsyncMock(return_value=True))

    await button.callback(interaction)

    assert game.status is models.EMatchStatus.WIN
    assert embed.color == discord.Color.green()
    assert button.style == discord.ButtonStyle.green
    assert str(button.emoji) == "✔️"
    assert dummy_response.edit_calls


@pytest.mark.asyncio
async def test_trivia_view_rejects_wrong_user(monkeypatch: pytest.MonkeyPatch) -> None:
    user = mocks.DummyUser(user_id=5)
    game = TriviaGame(player=user)
    game._match_id = 21
    game._correct_answer = "Correct"
    game._incorrect_answers = ["Wrong"]

    view = TriviaView(game=game, timeout=5.0)
    interaction = mocks.DummyInteraction(user=mocks.DummyUser(user_id=99))

    update_match_mock = AsyncMock(return_value=True)
    monkeypatch.setattr("modules.trivia.game.update_match", update_match_mock)

    await view.interaction_check(interaction)

    assert interaction.response.send_message.await_count == 1
    _, kwargs = interaction.response.send_message.call_args
    embed: discord.Embed | None = kwargs.get("embed") or (
        kwargs.get("embeds")[0] if kwargs.get("embeds") else None
    )

    assert embed is not None
    assert "You cannot respond to this game." == (embed.description or "")
    assert kwargs.get("ephemeral") is True
