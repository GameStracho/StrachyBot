from unittest.mock import MagicMock

import discord
import pytest

from modules.tic_tac_toe.game import TicTacToeGame
from shared.types import Position


def create_mock_user(user_id: int, name: str, is_bot: bool = False) -> discord.User:
    user = MagicMock(spec=discord.User)
    user.id = user_id
    user.display_name = name
    user.mention = f"<@{user_id}>"
    user.bot = is_bot
    return user


def test_is_opponent_bot() -> None:
    human = create_mock_user(101, "Alice", is_bot=False)
    bot_user = create_mock_user(202, "StrachyBot", is_bot=True)

    game_vs_bot = TicTacToeGame(player=human, opponent=bot_user, grid_size=3)
    assert game_vs_bot.is_opponent_bot() is True

    human2 = create_mock_user(303, "Bob", is_bot=False)
    game_vs_human = TicTacToeGame(player=human, opponent=human2, grid_size=3)
    assert game_vs_human.is_opponent_bot() is False


def test_bot_ai_center_or_corner_start() -> None:
    human = create_mock_user(101, "Alice", is_bot=False)
    bot_user = create_mock_user(202, "StrachyBot", is_bot=True)

    game = TicTacToeGame(player=human, opponent=bot_user, grid_size=3)
    # Human plays corner (0,0)
    assert game.play(Position(0, 0)) is True

    # Bot calculates move
    bot_pos = game.calculate_bot_move()
    assert bot_pos is not None
    # Center (1,1) is highest priority for 3x3
    assert bot_pos == Position(1, 1)


def test_bot_ai_immediate_block() -> None:
    human = create_mock_user(101, "Alice", is_bot=False)
    bot_user = create_mock_user(202, "StrachyBot", is_bot=True)

    game = TicTacToeGame(player=human, opponent=bot_user, grid_size=3)

    # Human plays (0,0) -> Bot plays (1,1)
    game.play(Position(0, 0))
    game.play(Position(1, 1))

    # Human plays (0,1) - Human now has (0,0) and (0,1), threatening (0,2) for 3-in-a-row win!
    game.play(Position(0, 1))

    # Bot calculates move
    bot_pos = game.calculate_bot_move()
    assert bot_pos is not None
    # Bot MUST block at (0,2)
    assert bot_pos == Position(0, 2)


def test_bot_ai_immediate_win() -> None:
    human = create_mock_user(101, "Alice", is_bot=False)
    bot_user = create_mock_user(202, "StrachyBot", is_bot=True)

    game = TicTacToeGame(player=human, opponent=bot_user, grid_size=3)

    # Move 0: Human plays (0,0)
    game.play(Position(0, 0))
    # Move 1: Bot plays (1,0)
    game.play(Position(1, 0))
    # Move 2: Human plays (0,1)
    game.play(Position(0, 1))
    # Move 3: Bot plays (1,1)
    game.play(Position(1, 1))
    # Move 4: Human plays (2,2) - Human fails to block bot line (1,0) - (1,1) -> (1,2)
    game.play(Position(2, 2))

    # Bot calculates move: Bot has (1,0) and (1,1), can win immediately at (1,2)
    bot_pos = game.calculate_bot_move()
    assert bot_pos is not None
    assert bot_pos == Position(1, 2)


@pytest.mark.parametrize("grid_size", [3, 4, 5])
def test_bot_ai_grid_sizes(grid_size: int) -> None:
    human = create_mock_user(101, "Alice", is_bot=False)
    bot_user = create_mock_user(202, "StrachyBot", is_bot=True)

    game = TicTacToeGame(player=human, opponent=bot_user, grid_size=grid_size)
    game.play(Position(0, 0))

    bot_pos = game.calculate_bot_move()
    assert bot_pos is not None
    assert 0 <= bot_pos.x < grid_size
    assert 0 <= bot_pos.y < grid_size
    assert bot_pos != Position(0, 0)
