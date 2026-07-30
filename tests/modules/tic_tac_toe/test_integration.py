from typing import Any, cast
from unittest.mock import AsyncMock

import discord
import pytest

from modules.tic_tac_toe import setup
from modules.tic_tac_toe.cogs import TicCog
from tests import mocks


@pytest.mark.asyncio
async def test_tic_cog_command_success(monkeypatch: pytest.MonkeyPatch) -> None:
    dummy_bot = mocks.DummyStrachyBot()
    cog = TicCog(bot=dummy_bot)

    player = mocks.create_dummy_user(100, "Alice", is_bot=False)
    opponent = mocks.create_dummy_user(200, "Bob", is_bot=False)

    interaction = mocks.DummyInteraction(user_id=100, username="Alice")
    interaction.user = player

    dummy_response_message = AsyncMock()
    interaction.original_response_message = dummy_response_message

    create_match_mock = AsyncMock(return_value=123)
    monkeypatch.setattr("modules.tic_tac_toe.cogs.create_match", create_match_mock)
    monkeypatch.setattr("modules.tic_tac_toe.cogs.helpers.execute_db_operation", mocks.execute_db_operation_mock)

    grid_choice = discord.app_commands.Choice(name="3x3", value=3)

    tic_tac_toe_callback = cast(Any, cog.tic_tac_toe.callback)
    await tic_tac_toe_callback(cog, interaction, opponent, grid_choice)

    assert interaction.response.send_message.called
    assert create_match_mock.called


@pytest.mark.asyncio
async def test_tic_cog_command_error_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    dummy_bot = mocks.DummyStrachyBot()
    cog = TicCog(bot=dummy_bot)

    opponent = mocks.create_dummy_user(200, "Bob")
    interaction = mocks.DummyInteraction(user_id=100, username="Alice")

    # Force error by raising during execute_db_operation
    monkeypatch.setattr("shared.helpers.execute_db_operation", AsyncMock(side_effect=Exception("DB Error")))
    handle_error_mock = AsyncMock()
    monkeypatch.setattr("shared.messages.handle_error", handle_error_mock)

    grid_choice = discord.app_commands.Choice(name="3x3", value=3)

    tic_tac_toe_callback = cast(Any, cog.tic_tac_toe.callback)
    await tic_tac_toe_callback(cog, interaction, opponent, grid_choice)

    assert handle_error_mock.called


@pytest.mark.asyncio
async def test_module_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    dummy_bot = mocks.DummyStrachyBot()
    add_cog_mock = AsyncMock()
    monkeypatch.setattr(dummy_bot, "add_cog", add_cog_mock)

    await setup(dummy_bot)

    assert add_cog_mock.called
