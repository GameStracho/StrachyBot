from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock

import discord
import pytest

from modules.tic_tac_toe.game import ETicTacToeCell, TicTacToeGame, TicTacToeGrid
from modules.tic_tac_toe.ui import (
    PLAYER_COLOR,
    TicTacToeButton,
    TicTacToeView,
    get_player_emojis,
)
from shared import ui
from shared.types import Position
from tests import mocks

# ---------------------------------------------------------------------------
# 1. Grid & Cell Unit Tests
# ---------------------------------------------------------------------------

def test_cell_enum_values() -> None:
    assert ETicTacToeCell.EMPTY.value == 0
    assert ETicTacToeCell.PLAYER.value == 1
    assert ETicTacToeCell.OPPONENT.value == 2


def test_grid_initialization_and_bounds() -> None:
    grid = TicTacToeGrid(size=3)
    assert grid.get_size() == 3

    # Initial cells empty
    for x in range(3):
        for y in range(3):
            assert grid.get_cell_value(Position(x, y)) == ETicTacToeCell.EMPTY

    # Out of bounds read returns None
    assert grid.get_cell_value(Position(-1, 0)) is None
    assert grid.get_cell_value(Position(3, 0)) is None
    assert grid.get_cell_value(Position(0, -1)) is None
    assert grid.get_cell_value(Position(0, 3)) is None

    # Set valid cell
    grid.set_cell_value(Position(1, 1), ETicTacToeCell.PLAYER)
    assert grid.get_cell_value(Position(1, 1)) == ETicTacToeCell.PLAYER

    # Set out of bounds does not raise or corrupt
    grid.set_cell_value(Position(-1, 0), ETicTacToeCell.OPPONENT)
    grid.set_cell_value(Position(4, 4), ETicTacToeCell.OPPONENT)


# ---------------------------------------------------------------------------
# 2. Game State & Logic Unit Tests
# ---------------------------------------------------------------------------

def test_game_initialization() -> None:
    player = mocks.create_dummy_user(100, "Alice")
    opponent = mocks.create_dummy_user(200, "Bob")
    game = TicTacToeGame(player=player, opponent=opponent, grid_size=3)

    assert game.match_id == -1
    assert game.get_player() == player
    assert game.get_opponent() == opponent
    assert game.get_total_moves() == 0
    assert game.get_grid_size() == 3
    assert game.get_winner() is None
    assert game.has_game_ended() is False
    assert game.is_players_turn() is True
    assert game.is_opponent_bot() is False
    assert "Tic-Tac-Toe game" in str(game)


def test_game_is_opponent_bot() -> None:
    human = mocks.create_dummy_user(100, "Alice", is_bot=False)
    bot = mocks.create_dummy_user(200, "StrachyBot", is_bot=True)
    game = TicTacToeGame(player=human, opponent=bot, grid_size=3)
    assert game.is_opponent_bot() is True


def test_game_invalid_moves() -> None:
    player = mocks.create_dummy_user(100, "Alice")
    opponent = mocks.create_dummy_user(200, "Bob")
    game = TicTacToeGame(player=player, opponent=opponent, grid_size=3)

    # Out of bounds
    assert game.play(Position(-1, 0)) is False
    assert game.play(Position(3, 3)) is False

    # Valid move
    assert game.play(Position(0, 0)) is True

    # Occupied cell
    assert game.play(Position(0, 0)) is False


def test_game_horizontal_win() -> None:
    player = mocks.create_dummy_user(100, "Alice")
    opponent = mocks.create_dummy_user(200, "Bob")
    game = TicTacToeGame(player=player, opponent=opponent, grid_size=3)

    assert game.play(Position(0, 0)) is True  # Player (turn 0)
    assert game.has_game_ended() is False
    assert game.play(Position(0, 1)) is True  # Opponent (turn 1)
    assert game.has_game_ended() is False
    assert game.play(Position(1, 0)) is True  # Player (turn 2)
    assert game.has_game_ended() is False
    assert game.play(Position(1, 1)) is True  # Opponent (turn 3)
    assert game.has_game_ended() is False
    assert game.play(Position(2, 0)) is True  # Player (turn 4)

    assert game.has_game_ended() is True
    assert game.get_winner() == player

    # Further move on finished game fails
    assert game.play(Position(2, 2)) is False


def test_game_vertical_win() -> None:
    player = mocks.create_dummy_user(100, "Alice")
    opponent = mocks.create_dummy_user(200, "Bob")
    game = TicTacToeGame(player=player, opponent=opponent, grid_size=3)

    game.play(Position(0, 0))  # Player (turn 0)
    assert game.has_game_ended() is False
    game.play(Position(1, 0))  # Opponent (turn 1)
    assert game.has_game_ended() is False
    game.play(Position(0, 1))  # Player (turn 2)
    assert game.has_game_ended() is False
    game.play(Position(1, 1))  # Opponent (turn 3)
    assert game.has_game_ended() is False
    game.play(Position(2, 2))  # Player (turn 4)
    assert game.has_game_ended() is False
    game.play(Position(1, 2))  # Opponent (turn 5)

    assert game.has_game_ended() is True
    assert game.get_winner() == opponent


def test_game_diagonal_wins() -> None:
    # Main diagonal: (0,0), (1,1), (2,2)
    player = mocks.create_dummy_user(100, "Alice")
    opponent = mocks.create_dummy_user(200, "Bob")
    game_main = TicTacToeGame(player=player, opponent=opponent, grid_size=3)
    game_main.play(Position(0, 0))  # Player (turn 0)
    assert game_main.has_game_ended() is False
    game_main.play(Position(0, 1))  # Opponent (turn 1)
    assert game_main.has_game_ended() is False
    game_main.play(Position(1, 1))  # Player (turn 2)
    assert game_main.has_game_ended() is False
    game_main.play(Position(0, 2))  # Opponent (turn 3)
    assert game_main.has_game_ended() is False
    game_main.play(Position(2, 2))  # Player (turn 4)

    assert game_main.has_game_ended() is True
    assert game_main.get_winner() == player

    # Anti-diagonal: (2,0), (1,1), (0,2)
    game_anti = TicTacToeGame(player=player, opponent=opponent, grid_size=3)
    game_anti.play(Position(2, 0))  # Player (turn 0)
    assert game_anti.has_game_ended() is False
    game_anti.play(Position(0, 0))  # Opponent (turn 1)
    assert game_anti.has_game_ended() is False
    game_anti.play(Position(1, 1))  # Player (turn 2)
    assert game_anti.has_game_ended() is False
    game_anti.play(Position(0, 1))  # Opponent (turn 3)
    assert game_anti.has_game_ended() is False
    game_anti.play(Position(0, 2))  # Player (turn 4)

    assert game_anti.has_game_ended() is True
    assert game_anti.get_winner() == player


def test_game_draw() -> None:
    player = mocks.create_dummy_user(100, "Alice")
    opponent = mocks.create_dummy_user(200, "Bob")
    game = TicTacToeGame(player=player, opponent=opponent, grid_size=3)

    moves = [
        Position(0, 0), Position(1, 0), Position(2, 0),
        Position(1, 1), Position(0, 1), Position(2, 1),
        Position(1, 2), Position(0, 2), Position(2, 2)
    ]
    for pos in moves:
        assert game.has_game_ended() is False
        game.play(pos)

    assert game.has_game_ended() is True
    assert game.get_winner() is None


# ---------------------------------------------------------------------------
# 3. Bot AI Unit Tests
# ---------------------------------------------------------------------------

def test_bot_ai_scoring_and_decisions() -> None:
    human = mocks.create_dummy_user(100, "Alice", is_bot=False)
    bot = mocks.create_dummy_user(200, "StrachyBot", is_bot=True)
    game = TicTacToeGame(player=human, opponent=bot, grid_size=3)

    # Move 0: Human plays (0,0)
    game.play(Position(0, 0))

    # Bot move should choose center (1,1)
    bot_pos = game.calculate_bot_move()
    assert bot_pos == Position(1, 1)

    # Test full grid calculation returns None
    for x in range(3):
        for y in range(3):
            game._grid.set_cell_value(Position(x, y), ETicTacToeCell.PLAYER)

    assert game.calculate_bot_move() is None


# ---------------------------------------------------------------------------
# 4. Emojis & UI Unit Tests
# ---------------------------------------------------------------------------

def test_get_player_emojis() -> None:
    # Valentine's day
    val_date = datetime(2026, 2, 14, tzinfo=timezone.utc)
    assert get_player_emojis(val_date) == ("💜", "🧡")

    # Regular day
    reg_date = datetime(2026, 7, 29, tzinfo=timezone.utc)
    assert get_player_emojis(reg_date) == ("🟣", "🟠")


@pytest.mark.asyncio
async def test_view_and_button_interaction_check() -> None:
    player = mocks.create_dummy_user(100, "Alice")
    opponent = mocks.create_dummy_user(200, "Bob")
    game = TicTacToeGame(player=player, opponent=opponent, grid_size=3)

    view = TicTacToeView(game=game, timeout=15.0)
    assert len(view.children) == 9
    assert view.get_game() == game

    # Eligible user check
    valid_interaction = mocks.DummyInteraction(user_id=100, username="Alice")
    assert await view.interaction_check(valid_interaction) is True

    # Ineligible user check
    invalid_interaction = mocks.DummyInteraction(user_id=999, username="Eve")
    assert await view.interaction_check(invalid_interaction) is False


@pytest.mark.asyncio
async def test_view_on_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    player = mocks.create_dummy_user(100, "Alice")
    opponent = mocks.create_dummy_user(200, "Bob")
    game = TicTacToeGame(player=player, opponent=opponent, grid_size=3)
    game.match_id = 42

    view = TicTacToeView(game=game, timeout=15.0)

    # Early return when message is None
    view.message = None
    await view.on_timeout()
    assert game.has_game_ended() is False

    # Setup dummy message with embed
    embed = discord.Embed(title="Tic-Tac-Toe")
    embed.add_field(name="Status", value="In progress")
    embed.add_field(name="Timeout", value="<t:1234:R>")
    message = AsyncMock()
    message.embeds = [embed]
    view.message = message

    monkeypatch.setattr("modules.tic_tac_toe.ui.update_match", AsyncMock(return_value=True))

    await view.on_timeout()

    assert embed.color == ui.TIMEOUT_COLOR
    assert message.edit.called
    for child in view.children:
        if isinstance(child, TicTacToeButton):
            assert child.disabled is True


@pytest.mark.asyncio
async def test_button_callback_human_and_bot_moves(monkeypatch: pytest.MonkeyPatch) -> None:
    human = mocks.create_dummy_user(100, "Alice", is_bot=False)
    bot = mocks.create_dummy_user(200, "StrachyBot", is_bot=True)
    game = TicTacToeGame(player=human, opponent=bot, grid_size=3)
    game.match_id = 99

    view = TicTacToeView(game=game, timeout=15.0)
    button = view.children[0]
    assert isinstance(button, TicTacToeButton)

    embed = discord.Embed(title="Tic-Tac-Toe")
    embed.add_field(name="Status", value="Start")
    embed.add_field(name="Timeout", value="<t:1234:R>")
    message = SimpleNamespace(embeds=[embed])

    interaction = mocks.DummyInteraction(user_id=100, username="Alice")
    interaction.message = cast(Any, message)

    monkeypatch.setattr("modules.tic_tac_toe.ui.update_match", AsyncMock(return_value=True))

    # Human plays button (0,0) -> triggers human move AND bot autoplay counter-move
    await button.callback(interaction)

    assert button.disabled is True
    assert game.get_total_moves() == 2  # Human move + Bot move
    assert interaction.response.edit_message.called


@pytest.mark.asyncio
async def test_button_callback_game_ended_win(monkeypatch: pytest.MonkeyPatch) -> None:
    player = mocks.create_dummy_user(100, "Alice")
    opponent = mocks.create_dummy_user(200, "Bob")
    game = TicTacToeGame(player=player, opponent=opponent, grid_size=3)
    game.match_id = 77

    # Setup game state 1 move away from player win: (0,0) and (1,0) filled by player
    game.play(Position(0, 0))  # Player (turn 0)
    game.play(Position(0, 1))  # Opponent (turn 1)
    game.play(Position(1, 0))  # Player (turn 2)
    game.play(Position(1, 1))  # Opponent (turn 3)
    assert game.has_game_ended() is False

    view = TicTacToeView(game=game, timeout=15.0)
    win_button = next(child for child in view.children if isinstance(child, TicTacToeButton) and child._position == Position(2, 0))

    embed = discord.Embed(title="Tic-Tac-Toe")
    embed.add_field(name="Status", value="In progress")
    embed.add_field(name="Timeout", value="<t:1234:R>")
    message = SimpleNamespace(embeds=[embed])

    interaction = mocks.DummyInteraction(user_id=100, username="Alice")
    interaction.message = cast(Any, message)

    update_match_mock = AsyncMock(return_value=True)
    monkeypatch.setattr("modules.tic_tac_toe.ui.update_match", update_match_mock)
    monkeypatch.setattr("modules.tic_tac_toe.ui.helpers.execute_db_operation", mocks.execute_db_operation_mock)

    await win_button.callback(interaction)

    assert game.has_game_ended() is True
    assert game.get_winner() == player
    assert embed.color == PLAYER_COLOR
    assert update_match_mock.called
