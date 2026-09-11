"""Alias module for shared.logger to preserve backwards compatibility."""

from .logger import (
    ANSI_ESCAPE_PATTERN,
    AsyncDatabaseLogHandler,
    ColoredFormatter,
    ModuleLogger,
    highlight,
    logger,
    setup_logger,
)

__all__ = [
    "ANSI_ESCAPE_PATTERN",
    "AsyncDatabaseLogHandler",
    "ColoredFormatter",
    "ModuleLogger",
    "highlight",
    "logger",
    "setup_logger",
]
