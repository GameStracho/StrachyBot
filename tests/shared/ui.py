from datetime import datetime, timezone

from tests.shared.ui import get_player_emojis


def test_get_player_emojis() -> None:
    # Valentine's day
    val_date = datetime(2026, 2, 14, tzinfo=timezone.utc)
    assert get_player_emojis(val_date) == ("💜", "🧡")

    # Regular day
    reg_date = datetime(2026, 7, 29, tzinfo=timezone.utc)
    assert get_player_emojis(reg_date) == ("🟣", "🟠")
