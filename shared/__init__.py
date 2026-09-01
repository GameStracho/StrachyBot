from typing import TYPE_CHECKING, Any

from . import api, database, logs, models, repository, types
from .database import db_manager
from .logger import logger

if TYPE_CHECKING:
    from bot import ui
    from bot.bot import StrachyBot
    from shared import bot

__all__ = [
    "StrachyBot",
    "api",
    "bot",
    "database",
    "db_manager",
    "helpers",
    "logger",
    "logs",
    "models",
    "repository",
    "types",
    "ui",
]


def __getattr__(name: str) -> Any:
    if name == "StrachyBot":
        from bot.bot import StrachyBot

        return StrachyBot
    if name == "ui":
        import bot.ui as ui

        return ui
    if name == "bot":
        from . import bot

        return bot
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
