import asyncio
import importlib
import os
from datetime import datetime
from typing import Any

import discord
import httpx
from discord import app_commands
from discord.ext import commands
from typing_extensions import override

from shared import db_manager, logger
from shared.logger import highlight
from shared.repository import create_command_log


class StrachyBot(commands.Bot):
    _start_time: datetime
    _http_client: httpx.AsyncClient | None
    _api_url: str

    def __init__(self, api_url: str | None = None) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", case_insensitive=True, intents=intents)

        self._start_time = discord.utils.utcnow()
        self._api_url = api_url or os.getenv("API_URL") or "http://localhost:8000"
        self._http_client = None

    @property
    def start_time(self) -> datetime:
        return self._start_time

    @property
    def api_url(self) -> str:
        return self._api_url

    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(base_url=self._api_url, timeout=10.0)
        return self._http_client

    @override
    async def close(self) -> None:
        """Called when the bot shuts down. Handles resource cleanup."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
        await db_manager.close()
        await super().close()

    @override
    async def setup_hook(self) -> None:
        """Called before the bot logs in."""
        # Initialize database singleton connection (if connection string configured)
        if os.getenv("CONNECTION_STRING"):
            db_manager.initialize()

        # Load shared database models
        try:
            importlib.import_module("shared.models")
            logger.debug("Shared database models loaded.")
        except Exception as e:
            logger.debug(f"Note on shared models import: {e}")

        # Load modules from bot/modules and legacy src/modules
        await self.__load_modules()

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
        # Fire-and-forget background DB task via the singleton instance if DB available
        if db_manager.db_session_factory:
            asyncio.create_task(
                db_manager.execute(
                    db_func=create_command_log,
                    user_id=interaction.user.id,
                    command_name=command.name,
                )
            )

    async def __load_modules(self) -> None:
        """
        Loads discord bot modules from bot/modules directory
        and legacy modules from src/modules for backwards compatibility.
        Modules are loaded strictly from __init__.py using the setup() function.
        """
        # 1. Load domain modules from bot/modules/
        bot_modules_dir: str = os.path.normpath(os.path.join(os.path.dirname(__file__), "modules"))
        if os.path.exists(bot_modules_dir):
            for module_name in os.listdir(bot_modules_dir):
                module_path = os.path.join(bot_modules_dir, module_name)
                if (
                    not os.path.isdir(module_path)
                    or module_name.startswith("_")
                    or not os.path.exists(os.path.join(module_path, "__init__.py"))
                ):
                    continue

                try:
                    await self.load_extension(f"bot.modules.{module_name}")
                    logger.info(f"Loaded bot module '{module_name}'.")
                except Exception as e:
                    logger.critical(f"Failed to load bot module '{module_name}': {e}")

        # 2. Load legacy cogs from src/modules/
        src_modules_dir: str = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "src", "modules")
        )
        if os.path.exists(src_modules_dir):
            for module_name in os.listdir(src_modules_dir):
                module_path = os.path.join(src_modules_dir, module_name)

                if (
                    not os.path.isdir(module_path)
                    or module_name.startswith("_")
                    or not os.path.exists(os.path.join(module_path, "cogs.py"))
                ):
                    continue

                try:
                    await self.load_extension(f"src.modules.{module_name}")
                    if os.path.exists(os.path.join(module_path, "models.py")):
                        importlib.import_module(f"src.modules.{module_name}.models")
                    logger.info(f"Legacy module '{module_name}' successfully loaded.")
                except Exception as e:
                    logger.critical(f"Failed to load legacy module '{module_name}': {e}.")
