import asyncio
import importlib
import os
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any, Concatenate, ParamSpec, TypeVar

import discord
from colorama import Fore
from discord import app_commands
from discord.ext import commands
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

import console

from .database import create_db_engine, create_session_factory
from .logs import logger
from .repository import create_command_log

P = ParamSpec("P")  # parameter type
R = TypeVar("R")  # result value type


class StrachyBot(commands.Bot):
    start_time: datetime = discord.utils.utcnow()
    _db_session_factory: async_sessionmaker[AsyncSession] | None
    _db_engine: AsyncEngine | None

    def __init__(self) -> None:
        # Setup intents
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix="!", case_insensitive=True, intents=intents)

        self._db_session_factory = None
        self._db_engine = None

    def create_db_session_factory(self, db_engine: AsyncEngine | None = None) -> None:
        """
        Create database session factory from a db_engine for accessing the database.
        Creates a new engine if db_engine is None.
        """

        logger.debug("YEP")

        if not db_engine:
            db_engine = create_db_engine()

        assert db_engine

        self._db_engine = db_engine
        self._db_session_factory = create_session_factory(db_engine)

    @property
    def db_session_factory(self) -> async_sessionmaker[AsyncSession] | None:
        return self._db_session_factory

    async def execute_db_operation(
        self,
        db_func: Callable[Concatenate[AsyncSession, P], Awaitable[R]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R | None:
        """
        Executes an async database operation with an AsyncSession.

        Automatically resolves the StrachyBot instance from target if given a
        discord.Interaction or discord.Message.

        :param target: StrachyBot instance, discord.Interaction, or discord.Message.
        :param db_func: Async function that takes `session: AsyncSession` as its first argument.
        :param args: Positional arguments passed to db_func after `session`.
        :param kwargs: Keyword arguments passed to db_func.
        :return: Result of db_func execution, or None if session factory is unavailable.
        """

        if not self._db_session_factory:
            return None

        async with self._db_session_factory() as session:
            if session:
                return await db_func(session, *args, **kwargs)

        return None

    async def close(self) -> None:
        """Called when the bot shuts down. Handles resource cleanup."""
        if self._db_engine is not None:
            logger.info("Disposing database engine connection pool...")
            await self._db_engine.dispose()
            logger.debug("Database engine successfully disposed.")

        await super().close()

    async def setup_hook(self) -> None:
        """Called before the bot logs in."""
        await self.__load_modules()

        # import shared database models
        importlib.import_module("shared.models")
        logger.debug("Shared database models loaded.")

        # sync commands with Discord
        synced: list[app_commands.AppCommand] = await self.tree.sync()
        synced_commands: str = ""
        for command in synced:
            if len(synced_commands):
                synced_commands += f", {command.name}"
            else:
                synced_commands += command.name

        logger.info(f"Slash commands synced: {console.highlight(Fore.YELLOW, synced_commands)}")

    async def on_ready(self) -> None:
        """Called when the bot starts."""
        logger.info(
            console.highlight(Fore.YELLOW, str(self.user)) + " is now online and ready to serve!"
        )

    async def on_app_command_completion(
        self, interaction: discord.Interaction, command: discord.app_commands.Command[Any, Any, Any]
    ) -> None:
        """Fired automatically whenever any slash command completes successfully!"""

        # Fire-and-forget background DB task to log usage
        asyncio.create_task(
            self.execute_db_operation(
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

            # Skip non-directories and utility modules
            if (
                not os.path.isdir(module_path)
                or module_name.startswith("_")
                or not os.path.join(module_path, "cogs.py")
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
