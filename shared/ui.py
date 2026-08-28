from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bot import ui
    from bot.ui import (
        COLORS,
        EMOJIS,
        ConfirmView,
        embed,
        get_player_colors,
        get_player_emojis,
        get_timeout_timestamp,
        get_user,
        handle_error,
        load_attachment,
    )

__all__ = [
    "COLORS",
    "EMOJIS",
    "ConfirmView",
    "embed",
    "get_player_colors",
    "get_player_emojis",
    "get_timeout_timestamp",
    "get_user",
    "handle_error",
    "load_attachment",
    "ui",
]


def __getattr__(name: str) -> Any:
    import bot.ui as bot_ui

    if name == "ui":
        return bot_ui
    if hasattr(bot_ui, name):
        return getattr(bot_ui, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
