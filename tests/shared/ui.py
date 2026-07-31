from datetime import datetime, timezone

from shared.ui import get_player_emojis


def test_get_player_emojis() -> None:
    # New Year
    assert get_player_emojis(datetime(2026, 12, 31, tzinfo=timezone.utc)) == ("🎇", "🎆")
    assert get_player_emojis(datetime(2027, 1, 1, tzinfo=timezone.utc)) == ("🎇", "🎆")

    # Valentine's day
    assert get_player_emojis(datetime(2026, 2, 14, tzinfo=timezone.utc)) == ("💜", "🧡")

    # April fools
    assert get_player_emojis(datetime(2026, 4, 1, tzinfo=timezone.utc)) == ("🤡", "🤪")
    assert get_player_emojis(datetime(2027, 4, 1, tzinfo=timezone.utc)) == ("🤡", "🤪")

    # Easter start
    assert get_player_emojis(datetime(2025, 4, 13, tzinfo=timezone.utc)) == ("🐰", "🐣")
    assert get_player_emojis(datetime(2026, 3, 29, tzinfo=timezone.utc)) == ("🐰", "🐣")
    assert get_player_emojis(datetime(2027, 3, 21, tzinfo=timezone.utc)) == ("🐰", "🐣")
    assert get_player_emojis(datetime(2028, 4, 9, tzinfo=timezone.utc)) == ("🐰", "🐣")

    # Easter end
    assert get_player_emojis(datetime(2025, 4, 27, tzinfo=timezone.utc)) == ("🐰", "🐣")
    assert get_player_emojis(datetime(2026, 4, 12, tzinfo=timezone.utc)) == ("🐰", "🐣")
    assert get_player_emojis(datetime(2027, 4, 4, tzinfo=timezone.utc)) == ("🐰", "🐣")
    assert get_player_emojis(datetime(2028, 4, 23, tzinfo=timezone.utc)) == ("🐰", "🐣")

    # Summer
    assert get_player_emojis(datetime(2028, 6, 4, tzinfo=timezone.utc)) == ("☀️", "🌊")
    assert get_player_emojis(datetime(2028, 7, 21, tzinfo=timezone.utc)) == ("☀️", "🌊")
    assert get_player_emojis(datetime(2028, 8, 12, tzinfo=timezone.utc)) == ("☀️", "🌊")

    # Halloween
    assert get_player_emojis(datetime(2028, 10, 31, tzinfo=timezone.utc)) == ("🎃", "👻")
    assert get_player_emojis(datetime(2028, 10, 12, tzinfo=timezone.utc)) == ("🎃", "👻")

    # Christmas
    assert get_player_emojis(datetime(2028, 12, 6, tzinfo=timezone.utc)) == ("⛄", "🎄")
    assert get_player_emojis(datetime(2028, 12, 24, tzinfo=timezone.utc)) == ("⛄", "🎄")
    assert get_player_emojis(datetime(2028, 12, 25, tzinfo=timezone.utc)) == ("⛄", "🎄")
    assert get_player_emojis(datetime(2028, 12, 26, tzinfo=timezone.utc)) == ("⛄", "🎄")

    # Regular day
    assert get_player_emojis(datetime(2026, 9, 29, tzinfo=timezone.utc)) == ("🟣", "🟠")
