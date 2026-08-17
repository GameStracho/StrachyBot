import asyncio
import importlib
import os
from datetime import UTC, datetime, timedelta
from typing import Any, ParamSpec, TypeVar

import discord
from discord import app_commands
from discord.ext import commands, tasks
from typing_extensions import override

from .database import db_manager
from .logs import highlight, logger
from .repository import create_command_log, delete_expired_logs

P = ParamSpec("P")  # parameter type
R = TypeVar("R")  # result value type


class StrachyBot(commands.Bot):
    _start_time: datetime

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", case_insensitive=True, intents=intents)

        self._start_time = discord.utils.utcnow()

    @property
    def start_time(self) -> datetime:
        return self._start_time

    @override
    async def close(self) -> None:
        """Called when the bot shuts down. Handles resource cleanup."""
        await db_manager.close()
        await super().close()

    @override
    async def setup_hook(self) -> None:
        """Called before the bot logs in."""
        # Initialize database singleton connection
        db_manager.initialize()
        await self.cleanup_old_logs_task()

        await self.__load_modules()

        # Import shared database models
        importlib.import_module("shared.models")
        logger.debug("Shared database models loaded.")

        # Sync commands with Discord
        synced: list[app_commands.AppCommand] = await self.tree.sync()
        synced_commands: str = ", ".join(command.name for command in synced)

        logger.info(f"Slash commands synced: {highlight(synced_commands)}")

    async def on_ready(self) -> None:
        """Called when the bot starts."""
        logger.info(f"{highlight(str(self.user))} is now online and ready to serve!")

    async def on_app_command_completion(
        self, interaction: discord.Interaction, command: discord.app_commands.Command[Any, Any, Any]
    ) -> None:
        """Fired automatically whenever any slash command completes successfully!"""
        # Fire-and-forget background DB task via the singleton instance
        asyncio.create_task(
            db_manager.execute(
                db_func=create_command_log,
                user_id=interaction.user.id,
                command_name=command.name,
            )
        )

    async def __load_modules(self) -> None:
        """Load all modules from src/modules directory."""
        modules_dir: str = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "modules")
        )
        success: bool = True

        for module_name in os.listdir(modules_dir):
            module_path = os.path.join(modules_dir, module_name)

            if (
                not os.path.isdir(module_path)
                or module_name.startswith("_")
                or not os.path.exists(os.path.join(module_path, "cogs.py"))
            ):
                continue

            try:
                # Load existing cogs from '__init.py__'
                if os.path.exists(os.path.join(module_path, "cogs.py")):
                    await self.load_extension(f"modules.{module_name}")
                    logger.debug(f"Loaded cog file for module '{module_name}'.")

                # Import database models from 'models.py'
                if os.path.exists(os.path.join(module_path, "models.py")):
                    importlib.import_module(f"modules.{module_name}.models")
                    logger.debug(f"Registered database models for module '{module_name}'.")

                logger.info(f"Module '{module_name}' successfully loaded.")
            except Exception as e:
                logger.critical(f"Failed to load module '{module_name}': {e}.")
                success = False

        if success:
            logger.info("All modules loaded.")

    @tasks.loop(hours=24)
    async def cleanup_old_logs_task(self) -> None:
        """Deletes database logs older than 7 days once per day."""
        cutoff_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=7)

        deleted_rows: int | None = await db_manager.execute(
            db_func=delete_expired_logs, cutoff=cutoff_date
        )

        if deleted_rows:
            logger.info(f"Cleaned up {deleted_rows} logs older than 7 days.")
