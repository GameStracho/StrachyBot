from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock

import discord
import pytest

from modules.tic_tac_toe.game import ETicTacToeCell, TicTacToeGame, TicTacToeGrid
from modules.tic_tac_toe.ui import (
    TicTacToeButton,
    TicTacToeView,
)
from shared import ui
from shared.models import EMatchStatus
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
    assert grid.size == 3

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
    player = mocks.DummyUser(user_id=100, username="Alice")
    opponent = mocks.DummyUser(user_id=200, username="Bob")
    game = TicTacToeGame(player=player, opponent=opponent, grid_size=3)

    assert game.match_id == -1
    assert game.player == player
    assert game.opponent == opponent
    assert game.total_moves == 0
    assert game.grid_size == 3
    assert game.status is EMatchStatus.PENDING
    assert game.is_players_turn is True
    assert "Tic-Tac-Toe game" in str(game)


@pytest.mark.asyncio
async def test_game_invalid_moves() -> None:
    player = mocks.DummyUser(user_id=100, username="Alice")
    opponent = mocks.DummyUser(user_id=200, username="Bob")
    game = TicTacToeGame(player=player, opponent=opponent, grid_size=3)

    # Out of bounds
    assert await game.play(Position(-1, 0)) is False
    assert await game.play(Position(3, 3)) is False

    # Valid move
    assert await game.play(Position(0, 0)) is True

    # Occupied cell
    assert await game.play(Position(0, 0)) is False


@pytest.mark.asyncio
async def test_game_horizontal_win() -> None:
    player = mocks.DummyUser(user_id=100, username="Alice")
    opponent = mocks.DummyUser(user_id=200, username="Bob")
    game = TicTacToeGame(player=player, opponent=opponent, grid_size=3)

    assert await game.play(Position(0, 0)) is True  # Player (turn 0)
    assert game._status == EMatchStatus.PENDING

    assert await game.play(Position(0, 1)) is True  # Opponent (turn 1)
    assert game._status == EMatchStatus.PENDING

    assert await game.play(Position(1, 0)) is True  # Player (turn 2)
    assert game._status == EMatchStatus.PENDING

    assert await game.play(Position(1, 1)) is True  # Opponent (turn 3)
    assert game._status == EMatchStatus.PENDING

    assert await game.play(Position(2, 0)) is True  # Player (turn 4)
    assert game.status == EMatchStatus.WIN
    assert game.winner == player

    # Further move on finished game fails
    assert await game.play(Position(2, 2)) is False


@pytest.mark.asyncio
async def test_game_vertical_win() -> None:
    player = mocks.DummyUser(user_id=100, username="Alice")
    opponent = mocks.DummyUser(user_id=200, username="Bob")
    game = TicTacToeGame(player=player, opponent=opponent, grid_size=3)

    await game.play(Position(0, 0))  # Player (turn 0)
    assert game._status == EMatchStatus.PENDING

    await game.play(Position(1, 0))  # Opponent (turn 1)
    assert game._status == EMatchStatus.PENDING

    await game.play(Position(0, 1))  # Player (turn 2)
    assert game._status == EMatchStatus.PENDING

    await game.play(Position(1, 1))  # Opponent (turn 3)
    assert game._status == EMatchStatus.PENDING

    await game.play(Position(2, 2))  # Player (turn 4)
    assert game._status == EMatchStatus.PENDING

    await game.play(Position(1, 2))  # Opponent (turn 5)
    assert game.status == EMatchStatus.LOSS
    assert game.winner == opponent


@pytest.mark.asyncio
async def test_game_diagonal_wins() -> None:
    # Main diagonal: (0,0), (1,1), (2,2)
    player = mocks.DummyUser(user_id=100, username="Alice")
    opponent = mocks.DummyUser(user_id=200, username="Bob")
    game_main = TicTacToeGame(player=player, opponent=opponent, grid_size=3)
    await game_main.play(Position(0, 0))  # Player (turn 0)
    assert game_main._status == EMatchStatus.PENDING

    await game_main.play(Position(0, 1))  # Opponent (turn 1)
    assert game_main._status == EMatchStatus.PENDING

    await game_main.play(Position(1, 1))  # Player (turn 2)
    assert game_main._status == EMatchStatus.PENDING

    await game_main.play(Position(0, 2))  # Opponent (turn 3)
    assert game_main._status == EMatchStatus.PENDING

    await game_main.play(Position(2, 2))  # Player (turn 4)
    assert game_main.status == EMatchStatus.WIN
    assert game_main.winner == player

    # Anti-diagonal: (2,0), (1,1), (0,2)
    game_anti = TicTacToeGame(player=player, opponent=opponent, grid_size=3)

    await game_anti.play(Position(2, 0))  # Player (turn 0)
    assert game_anti._status == EMatchStatus.PENDING

    await game_anti.play(Position(0, 0))  # Opponent (turn 1)
    assert game_anti._status == EMatchStatus.PENDING

    await game_anti.play(Position(1, 1))  # Player (turn 2)
    assert game_anti._status == EMatchStatus.PENDING

    await game_anti.play(Position(0, 1))  # Opponent (turn 3)
    assert game_anti._status == EMatchStatus.PENDING

    await game_anti.play(Position(0, 2))  # Player (turn 4)
    assert game_anti.status == EMatchStatus.WIN
    assert game_anti.winner == player


@pytest.mark.asyncio
async def test_game_draw() -> None:
    player = mocks.DummyUser(user_id=100, username="Alice")
    opponent = mocks.DummyUser(user_id=200, username="Bob")
    game = TicTacToeGame(player=player, opponent=opponent, grid_size=3)

    moves = [
        Position(0, 0),
        Position(1, 0),
        Position(2, 0),
        Position(1, 1),
        Position(0, 1),
        Position(2, 1),
        Position(1, 2),
        Position(0, 2),
        Position(2, 2),
    ]
    for pos in moves:
        assert game.status is EMatchStatus.PENDING
        await game.play(pos)

    assert game.status is EMatchStatus.DRAW
    assert game.winner is None


# ---------------------------------------------------------------------------
# 3. Bot AI Unit Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bot_ai_scoring_and_decisions() -> None:
    human = mocks.DummyUser(user_id=100, username="Alice", is_bot=False)
    bot = mocks.DummyUser(user_id=200, username="StrachyBot", is_bot=True)
    game = TicTacToeGame(player=human, opponent=bot, grid_size=3)

    # Move 0: Human plays (0,0)
    await game.play(Position(0, 0))

    # Bot move should choose center (1,1)
    bot_pos = game.calculate_bot_move()
    assert bot_pos == Position(1, 1)

    # Test full grid calculation returns None
    for x in range(3):
        for y in range(3):
            game._grid.set_cell_value(Position(x, y), ETicTacToeCell.PLAYER)

    assert game.calculate_bot_move() is None


@pytest.mark.asyncio
async def test_bot_ai_center_or_corner_start() -> None:
    human = mocks.DummyUser(user_id=101, username="Alice", is_bot=False)
    bot_user = mocks.DummyUser(user_id=202, username="StrachyBot", is_bot=True)

    game = TicTacToeGame(player=human, opponent=bot_user, grid_size=3)
    # Human plays corner (0,0)
    assert await game.play(Position(0, 0)) is True

    # Bot calculates move
    bot_pos = game.calculate_bot_move()
    assert bot_pos is not None
    # Center (1,1) is highest priority for 3x3
    assert bot_pos == Position(1, 1)


@pytest.mark.asyncio
async def test_bot_ai_immediate_block() -> None:
    human = mocks.DummyUser(user_id=101, username="Alice", is_bot=False)
    bot_user = mocks.DummyUser(user_id=202, username="StrachyBot", is_bot=True)

    game = TicTacToeGame(player=human, opponent=bot_user, grid_size=3)

    # Human plays (0,0) -> Bot plays (1,1)
    await game.play(Position(0, 0))
    await game.play(Position(1, 1))

    # Human plays (0,1) - Human now has (0,0) and (0,1), threatening (0,2) for 3-in-a-row win!
    await game.play(Position(0, 1))

    # Bot calculates move
    bot_pos = game.calculate_bot_move()
    assert bot_pos is not None
    # Bot MUST block at (0,2)
    assert bot_pos == Position(0, 2)


@pytest.mark.asyncio
async def test_bot_ai_immediate_win() -> None:
    human = mocks.DummyUser(user_id=101, username="Alice", is_bot=False)
    bot_user = mocks.DummyUser(user_id=202, username="StrachyBot", is_bot=True)

    game = TicTacToeGame(player=human, opponent=bot_user, grid_size=3)

    # Move 0: Human plays (0,0)
    await game.play(Position(0, 0))
    # Move 1: Bot plays (1,0)
    await game.play(Position(1, 0))
    # Move 2: Human plays (0,1)
    await game.play(Position(0, 1))
    # Move 3: Bot plays (1,1)
    await game.play(Position(1, 1))
    # Move 4: Human plays (2,2) - Human fails to block bot line (1,0) - (1,1) -> (1,2)
    await game.play(Position(2, 2))

    # Bot calculates move: Bot has (1,0) and (1,1), can win immediately at (1,2)
    bot_pos = game.calculate_bot_move()
    assert bot_pos is not None
    assert bot_pos == Position(1, 2)


@pytest.mark.asyncio
@pytest.mark.parametrize("grid_size", [3, 4, 5])
async def test_bot_ai_grid_sizes(grid_size: int) -> None:
    human = mocks.DummyUser(user_id=101, username="Alice", is_bot=False)
    bot_user = mocks.DummyUser(user_id=202, username="StrachyBot", is_bot=True)

    game = TicTacToeGame(player=human, opponent=bot_user, grid_size=grid_size)
    await game.play(Position(0, 0))

    bot_pos = game.calculate_bot_move()
    assert bot_pos is not None
    assert 0 <= bot_pos.x < grid_size
    assert 0 <= bot_pos.y < grid_size
    assert bot_pos != Position(0, 0)


# ---------------------------------------------------------------------------
# 4. UI Unit Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_view_and_button_interaction_check() -> None:
    player = mocks.DummyUser(user_id=100, username="Alice")
    opponent = mocks.DummyUser(user_id=200, username="Bob")
    game = TicTacToeGame(player=player, opponent=opponent, grid_size=3)

    view = TicTacToeView(game=game, timeout=15.0)
    assert len(view.children) == 9
    assert view.game == game

    # Eligible user check
    valid_interaction = mocks.DummyInteraction(user=player)
    assert await view.interaction_check(valid_interaction) is True

    # Ineligible user check
    invalid_interaction = mocks.DummyInteraction(user=mocks.DummyUser(user_id=999, username="Eve"))
    assert await view.interaction_check(invalid_interaction) is False


@pytest.mark.asyncio
async def test_view_on_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    player = mocks.DummyUser(user_id=100, username="Alice")
    opponent = mocks.DummyUser(user_id=200, username="Bob")
    game = TicTacToeGame(player=player, opponent=opponent, grid_size=3)
    game._match_id = 42

    view = TicTacToeView(game=game, timeout=15.0)

    # Early return when message is None
    view.message = None
    await view.on_timeout()
    assert game.status is EMatchStatus.PENDING

    # Setup dummy message with embed
    embed = discord.Embed(title="Tic-Tac-Toe")
    embed.add_field(name="Status", value="In progress")
    embed.add_field(name="Timeout", value="<t:1234:R>")
    message = AsyncMock()
    message.embeds = [embed]
    view.message = message

    monkeypatch.setattr("modules.tic_tac_toe.game.update_match", AsyncMock(return_value=True))

    await view.on_timeout()

    assert embed.color == ui.COLORS["game_timeout"]
    assert message.edit.called
    for child in view.children:
        if isinstance(child, TicTacToeButton):
            assert child.disabled is True


@pytest.mark.asyncio
async def test_button_callback_human_and_bot_moves(monkeypatch: pytest.MonkeyPatch) -> None:
    player = mocks.DummyUser(user_id=100, username="Alice", is_bot=False)
    bot = mocks.DummyUser(user_id=200, username="StrachyBot", is_bot=True)
    game = TicTacToeGame(player=player, opponent=bot, grid_size=3)
    game._match_id = 99

    view = TicTacToeView(game=game, timeout=15.0)
    button = view.children[0]
    assert isinstance(button, TicTacToeButton)

    embed = discord.Embed(title="Tic-Tac-Toe")
    embed.add_field(name="Status", value="Start")
    embed.add_field(name="Timeout", value="<t:1234:R>")
    message = SimpleNamespace(embeds=[embed])

    interaction = mocks.DummyInteraction(user=player)
    interaction.message = cast(Any, message)

    monkeypatch.setattr("modules.tic_tac_toe.game.update_match", AsyncMock(return_value=True))

    # Human plays button (0,0) -> triggers human move AND bot autoplay counter-move
    await button.callback(interaction)

    assert button.disabled is True
    assert game.total_moves == 2  # Human move + Bot move
    assert interaction.response.edit_message.called


@pytest.mark.asyncio
async def test_button_callback_game_ended_win(monkeypatch: pytest.MonkeyPatch) -> None:
    player = mocks.DummyUser(user_id=100, username="Alice")
    opponent = mocks.DummyUser(user_id=200, username="Bob")
    game = TicTacToeGame(player=player, opponent=opponent, grid_size=3)
    game._match_id = 77
    game._bot = mocks.DummyStrachyBot()

    # Setup game state 1 move away from player win: (0,0) and (1,0) filled by player
    await game.play(Position(0, 0))  # Player (turn 0)
    await game.play(Position(0, 1))  # Opponent (turn 1)
    await game.play(Position(1, 0))  # Player (turn 2)
    await game.play(Position(1, 1))  # Opponent (turn 3)
    assert game.status is EMatchStatus.PENDING

    view = TicTacToeView(game=game, timeout=15.0)
    win_button = next(
        child
        for child in view.children
        if isinstance(child, TicTacToeButton) and child._position == Position(2, 0)
    )

    embed = discord.Embed(title="Tic-Tac-Toe")
    embed.add_field(name="Status", value="In progress")
    embed.add_field(name="Timeout", value="<t:1234:R>")
    message = SimpleNamespace(embeds=[embed])

    interaction = mocks.DummyInteraction(user=player)
    interaction.message = cast(Any, message)

    update_match_mock = AsyncMock(return_value=True)
    monkeypatch.setattr("modules.tic_tac_toe.game.update_match", update_match_mock)
    monkeypatch.setattr(
        "modules.tic_tac_toe.game.execute_db_operation", mocks.dummy_execute_db_operation
    )

    await win_button.callback(interaction)
    player_color, _ = ui.get_player_colors()

    assert game._status is EMatchStatus.WIN
    assert game.winner == player
    assert embed.color == player_color
    assert update_match_mock.called
