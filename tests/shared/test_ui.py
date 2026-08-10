from datetime import UTC, datetime

import discord

from shared.ui import COLORS, get_player_colors, get_player_emojis


def test_get_player_colors() -> None:
    # New Year
    assert get_player_colors(datetime(2026, 12, 31, tzinfo=UTC)) == (
        discord.Color.red(),
        discord.Color.blue(),
    )
    assert get_player_colors(datetime(2027, 1, 1, tzinfo=UTC)) == (
        discord.Color.red(),
        discord.Color.blue(),
    )

    # Valentine's day
    assert get_player_colors(datetime(2026, 2, 14, tzinfo=UTC)) == (
        discord.Color.purple(),
        discord.Color.orange(),
    )

    # April fools
    assert get_player_colors(datetime(2026, 4, 1, tzinfo=UTC)) == (
        discord.Color.yellow(),
        COLORS["white"],
    )
    assert get_player_colors(datetime(2027, 4, 1, tzinfo=UTC)) == (
        discord.Color.yellow(),
        COLORS["white"],
    )

    # Easter start
    assert get_player_colors(datetime(2025, 4, 13, tzinfo=UTC)) == (
        COLORS["white"],
        discord.Color.yellow(),
    )
    assert get_player_colors(datetime(2026, 3, 29, tzinfo=UTC)) == (
        COLORS["white"],
        discord.Color.yellow(),
    )
    assert get_player_colors(datetime(2027, 3, 21, tzinfo=UTC)) == (
        COLORS["white"],
        discord.Color.yellow(),
    )
    assert get_player_colors(datetime(2028, 4, 9, tzinfo=UTC)) == (
        COLORS["white"],
        discord.Color.yellow(),
    )

    # Easter end
    assert get_player_colors(datetime(2025, 4, 27, tzinfo=UTC)) == (
        COLORS["white"],
        discord.Color.yellow(),
    )
    assert get_player_colors(datetime(2026, 4, 12, tzinfo=UTC)) == (
        COLORS["white"],
        discord.Color.yellow(),
    )
    assert get_player_colors(datetime(2027, 4, 4, tzinfo=UTC)) == (
        COLORS["white"],
        discord.Color.yellow(),
    )
    assert get_player_colors(datetime(2028, 4, 23, tzinfo=UTC)) == (
        COLORS["white"],
        discord.Color.yellow(),
    )

    # Star Wars day
    assert get_player_colors(datetime(2028, 5, 4, tzinfo=UTC)) == (
        discord.Color.blue(),
        discord.Color.red(),
    )

    # Summer
    assert get_player_colors(datetime(2028, 6, 4, tzinfo=UTC)) == (
        discord.Color.yellow(),
        discord.Color.blue(),
    )
    assert get_player_colors(datetime(2028, 7, 21, tzinfo=UTC)) == (
        discord.Color.yellow(),
        discord.Color.blue(),
    )
    assert get_player_colors(datetime(2028, 8, 12, tzinfo=UTC)) == (
        discord.Color.yellow(),
        discord.Color.blue(),
    )

    # Halloween
    assert get_player_colors(datetime(2028, 10, 31, tzinfo=UTC)) == (
        discord.Color.orange(),
        COLORS["brown"],
    )
    assert get_player_colors(datetime(2028, 10, 12, tzinfo=UTC)) == (
        discord.Color.orange(),
        COLORS["brown"],
    )

    # Christmas
    assert get_player_colors(datetime(2028, 12, 6, tzinfo=UTC)) == (
        discord.Color.red(),
        discord.Color.green(),
    )
    assert get_player_colors(datetime(2028, 12, 24, tzinfo=UTC)) == (
        discord.Color.red(),
        discord.Color.green(),
    )
    assert get_player_colors(datetime(2028, 12, 25, tzinfo=UTC)) == (
        discord.Color.red(),
        discord.Color.green(),
    )
    assert get_player_colors(datetime(2028, 12, 26, tzinfo=UTC)) == (
        discord.Color.red(),
        discord.Color.green(),
    )

    # Regular day
    assert get_player_colors(datetime(2026, 9, 29, tzinfo=UTC)) == (
        discord.Color.purple(),
        discord.Color.orange(),
    )


def test_get_player_emojis() -> None:
    # New Year
    assert get_player_emojis(datetime(2026, 12, 31, tzinfo=UTC)) == ("🎉", "🎆")
    assert get_player_emojis(datetime(2027, 1, 1, tzinfo=UTC)) == ("🎉", "🎆")

    # Valentine's day
    assert get_player_emojis(datetime(2026, 2, 14, tzinfo=UTC)) == ("💜", "🧡")

    # April fools
    assert get_player_emojis(datetime(2026, 4, 1, tzinfo=UTC)) == ("🤪", "🤡")
    assert get_player_emojis(datetime(2027, 4, 1, tzinfo=UTC)) == ("🤪", "🤡")

    # Easter start
    assert get_player_emojis(datetime(2025, 4, 13, tzinfo=UTC)) == ("🐰", "🐣")
    assert get_player_emojis(datetime(2026, 3, 29, tzinfo=UTC)) == ("🐰", "🐣")
    assert get_player_emojis(datetime(2027, 3, 21, tzinfo=UTC)) == ("🐰", "🐣")
    assert get_player_emojis(datetime(2028, 4, 9, tzinfo=UTC)) == ("🐰", "🐣")

    # Easter end
    assert get_player_emojis(datetime(2025, 4, 27, tzinfo=UTC)) == ("🐰", "🐣")
    assert get_player_emojis(datetime(2026, 4, 12, tzinfo=UTC)) == ("🐰", "🐣")
    assert get_player_emojis(datetime(2027, 4, 4, tzinfo=UTC)) == ("🐰", "🐣")
    assert get_player_emojis(datetime(2028, 4, 23, tzinfo=UTC)) == ("🐰", "🐣")

    # Star Wars day
    assert get_player_emojis(datetime(2028, 5, 4, tzinfo=UTC)) == ("🩵", "❤️")

    # Summer
    assert get_player_emojis(datetime(2028, 6, 4, tzinfo=UTC)) == ("☀️", "🌊")
    assert get_player_emojis(datetime(2028, 7, 21, tzinfo=UTC)) == ("☀️", "🌊")
    assert get_player_emojis(datetime(2028, 8, 12, tzinfo=UTC)) == ("☀️", "🌊")

    # Halloween
    assert get_player_emojis(datetime(2028, 10, 31, tzinfo=UTC)) == ("👻", "🦉")
    assert get_player_emojis(datetime(2028, 10, 12, tzinfo=UTC)) == ("👻", "🦉")

    # Christmas
    assert get_player_emojis(datetime(2028, 12, 6, tzinfo=UTC)) == ("🎁", "🎄")
    assert get_player_emojis(datetime(2028, 12, 24, tzinfo=UTC)) == ("🎁", "🎄")
    assert get_player_emojis(datetime(2028, 12, 25, tzinfo=UTC)) == ("🎁", "🎄")
    assert get_player_emojis(datetime(2028, 12, 26, tzinfo=UTC)) == ("🎁", "🎄")

    # Regular day
    assert get_player_emojis(datetime(2026, 9, 29, tzinfo=UTC)) == ("🟣", "🟠")
