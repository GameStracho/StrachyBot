from typing import Any, cast
from unittest.mock import AsyncMock, Mock

import discord
import pytest

from modules.wordle.cogs import WordleCog
from modules.wordle.game import WordleGame
from modules.wordle.ui import WordleView
from shared import bot, models
from tests import mocks


@pytest.mark.asyncio
async def test_wordle_cog_starts_game_and_sends_embed(monkeypatch: pytest.MonkeyPatch) -> None:
    interaction = mocks.DummyInteraction(user_id=13, username="Alice")
    interaction.user = mocks.create_dummy_user(13, "Alice")

    async def fake_create_match(*args: Any, **kwargs: Any) -> int:
        return 42

    monkeypatch.setattr(
        "modules.wordle.game.execute_db_operation", mocks.dummy_execute_db_operation
    )
    monkeypatch.setattr(
        "modules.wordle.cogs.execute_db_operation", mocks.dummy_execute_db_operation
    )
    monkeypatch.setattr("modules.wordle.game.create_match", fake_create_match)

    mock_msg = AsyncMock(spec=discord.Message)
    monkeypatch.setattr(interaction, "original_response", AsyncMock(return_value=mock_msg))

    cog = WordleCog(bot=bot.StrachyBot())
    wordle_callback = cast(Any, cog.wordle.callback)

    await wordle_callback(cog, interaction, False)

    assert interaction.response.send_message.await_count == 1
    assert cast(AsyncMock, interaction.original_response).await_count == 1


@pytest.mark.asyncio
async def test_wordle_cog_daily_challenge_not_played(monkeypatch: pytest.MonkeyPatch) -> None:
    interaction = mocks.DummyInteraction(user_id=13, username="Alice")
    interaction.user = mocks.create_dummy_user(13, "Alice")

    async def fake_execute_db_operation(
        target: Any, db_func: Any, *args: Any, **kwargs: Any
    ) -> Any:
        if db_func.__name__ == "has_played_daily_challenge":
            return False
        if db_func.__name__ == "create_match":
            return 42
        return await db_func(None, *args, **kwargs)

    monkeypatch.setattr("modules.wordle.cogs.execute_db_operation", fake_execute_db_operation)
    monkeypatch.setattr("modules.wordle.game.execute_db_operation", fake_execute_db_operation)

    cog = WordleCog(bot=bot.StrachyBot())
    wordle_callback = cast(Any, cog.wordle.callback)

    await wordle_callback(cog, interaction, True)

    assert interaction.response.send_message.await_count == 1


@pytest.mark.asyncio
async def test_wordle_cog_daily_challenge_already_played(monkeypatch: pytest.MonkeyPatch) -> None:
    interaction = mocks.DummyInteraction(user_id=13, username="Alice")
    interaction.user = mocks.create_dummy_user(13, "Alice")

    async def fake_execute_db_operation(
        target: Any, db_func: Any, *args: Any, **kwargs: Any
    ) -> Any:
        if db_func.__name__ == "has_played_daily_challenge":
            return True
        return None

    monkeypatch.setattr("modules.wordle.cogs.execute_db_operation", fake_execute_db_operation)

    cog = WordleCog(bot=bot.StrachyBot())
    wordle_callback = cast(Any, cog.wordle.callback)

    await wordle_callback(cog, interaction, True)

    assert interaction.response.send_message.await_count == 1
    _, kwargs = interaction.response.send_message.call_args
    assert "already played" in kwargs.get("content", "")
    assert kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_wordle_cog_error_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    interaction = mocks.DummyInteraction(user_id=13, username="Alice")
    interaction.user = mocks.create_dummy_user(13, "Alice")

    async def fake_execute_db_operation(*args: Any, **kwargs: Any) -> Any:
        raise mocks.TestError("DB Error")

    monkeypatch.setattr("modules.wordle.cogs.execute_db_operation", fake_execute_db_operation)

    error_mock = AsyncMock()
    monkeypatch.setattr("modules.wordle.cogs.ui.handle_error", error_mock)

    cog = WordleCog(bot=bot.StrachyBot())
    wordle_callback = cast(Any, cog.wordle.callback)

    await wordle_callback(cog, interaction, True)

    error_mock.assert_called_once()


@pytest.mark.asyncio
async def test_wordle_view_timeout_disables_buttons_and_updates_db(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    game = WordleGame(player_id=8, is_daily=False)
    game._match_id = 55
    game._secret_word = "apple"
    game._bot = mocks.DummyStrachyBot()

    view = WordleView(game=game, timeout=1.0)

    mock_message = AsyncMock(spec=discord.Message)
    mock_message.edit = AsyncMock(return_value=mock_message)
    mock_message._state._get_client = Mock(return_value=bot.StrachyBot())

    embed = discord.Embed(title="Wordle")
    embed.add_field(name="Timeout", value="active")
    embed.add_field(name="Status", value="active")
    mock_message.embeds = [embed]

    view.message = mock_message

    update_match_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(
        "modules.wordle.game.execute_db_operation", mocks.dummy_execute_db_operation
    )
    monkeypatch.setattr("modules.wordle.game.update_match", update_match_mock)

    await view.on_timeout()

    assert game.get_status() == models.EMatchStatus.TIMEOUT
    update_match_mock.assert_called_once()
    assert all(child.disabled for child in view.children if isinstance(child, discord.ui.Button))
