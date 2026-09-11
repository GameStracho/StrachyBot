from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bot.bot import StrachyBot

__all__ = ["StrachyBot"]


def __getattr__(name: str) -> Any:
    if name == "StrachyBot":
        from bot.bot import StrachyBot

        return StrachyBot
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
