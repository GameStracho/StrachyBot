from typing import Any, cast
from unittest.mock import AsyncMock, Mock

import discord
import pytest

from modules.trivia.cogs import TriviaCog
from modules.trivia.game import TriviaGame
from modules.trivia.models import ETriviaCategory, ETriviaDifficulty
from modules.trivia.ui import TriviaButton, TriviaView
from shared import bot, models
from tests import mocks


@pytest.mark.asyncio
async def test_trivia_cog_creates_game_and_sends_embed(monkeypatch: pytest.MonkeyPatch) -> None:
    interaction = mocks.DummyInteraction(user=mocks.DummyUser(user_id=13, username="Alice"))

    async def fake_fetch_api(self: TriviaGame) -> None:
        self._category = ETriviaCategory.VIDEO_GAMES
        self._difficulty = ETriviaDifficulty.MEDIUM
        self._question = "Which game has Master Chief?"
        self._correct_answer = "Halo"
        self._incorrect_answers = ["Minecraft", "Fortnite", "Tetris"]

    async def fake_create_match(*args: Any, **kwargs: Any) -> int:
        return 42

    monkeypatch.setattr(TriviaGame, "fetch_api", fake_fetch_api)
    monkeypatch.setattr("modules.trivia.game.create_match", fake_create_match)

    cog = TriviaCog(bot=bot.StrachyBot())

    trivia_callback = cast(Any, cog.trivia.callback)
    await trivia_callback(cog, interaction, ETriviaCategory.ANY, ETriviaDifficulty.ANY)

    assert interaction.response.defer.await_count == 1
    assert interaction.followup.send.await_count == 1


@pytest.mark.asyncio
async def test_view_timeout_disables_buttons_and_updates_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    game = TriviaGame(player=mocks.DummyUser(user_id=8))
    game._match_id = 55
    game._question = "Question"
    game._correct_answer = "Correct"
    game._incorrect_answers = ["Wrong"]

    view = TriviaView(game=game, timeout=1.0)

    # Configure the mock message to perfectly replicate an edit lifecycle
    mock_message = AsyncMock(spec=discord.Message)
    mock_message.edit = AsyncMock(return_value=mock_message)
    mock_message._state._get_client = Mock(return_value=bot.StrachyBot())
    view.message = mock_message

    monkeypatch.setattr("modules.trivia.game.update_match", AsyncMock(return_value=True))
    await view.on_timeout()

    assert game.status is models.EMatchStatus.TIMEOUT
    assert all(child.disabled for child in view.children if isinstance(child, TriviaButton))
