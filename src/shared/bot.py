import os
from typing import List
from colorama import Fore
from datetime import datetime
import importlib

import discord
from discord.ext import commands
from discord import app_commands
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, AsyncEngine

from shared import console, database

class StrachyBot(commands.Bot):
    start_time: datetime = discord.utils.utcnow()
    db_engine: AsyncEngine
    db_session_factory: async_sessionmaker[AsyncSession]

    def __init__(self, db_engine: AsyncEngine | None = None):
        # Setup intents
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix="!", case_insensitive=True, intents=intents)

        self.db_engine = db_engine if db_engine else database.create_db_engine()
        self.db_session_factory = database.create_session_factory(self.db_engine)


    async def setup_hook(self) -> None:
        """Called before the bot logs in."""
        await self.__load_modules()

        # import shared database models
        importlib.import_module("shared.models")
        console.log_debug("Shared database models loaded.")

        # create database tables
        async with self.db_engine.begin() as connection:
            await connection.run_sync(database.Base.metadata.create_all)
            console.log_success("Database tables synced.")

        # sync commands with Discord
        synced: List[app_commands.AppCommand] = await self.tree.sync()
        synced_commands: str = ""
        for command in synced:
            if len(synced_commands):
                synced_commands += f", {command.name}"
            else:
                synced_commands += command.name

        console.log_info(f"Slash commands synced: {console.highlight(Fore.YELLOW, synced_commands)}")


    async def on_ready(self) -> None:
        """Called when the bot starts."""
        console.log_success(console.highlight(Fore.YELLOW, str(self.user)) + " is now online and ready to serve!")


    async def __load_modules(self) -> None:
        """Load all modules from src/modules directory."""
        modules_dir: str = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "modules"))
        success: bool = True

        for module_name in os.listdir(modules_dir):
            module_path = os.path.join(modules_dir, module_name)
            
            # Skip non-directories and utility modules
            if not os.path.isdir(module_path) or module_name.startswith("_"):
                continue
            
            # Skip if cogs.py does not exist in the module
            cogs_file = os.path.join(module_path, "cogs.py")
            if not os.path.exists(cogs_file):
                continue

            try:
                # Load existing cogs from __init.py__ inside the module
                if os.path.exists(os.path.join(module_path, "cogs.py")):
                    await self.load_extension(f"modules.{module_name}")
                    console.log_debug(f"Loaded cog file for module '{module_name}'.")

                # Load existing cogs.py in the module
                if os.path.exists(os.path.join(module_path, "models.py")):
                    importlib.import_module(f"modules.{module_name}.models")
                    console.log_debug(f"Registered database models for module '{module_name}'.")

                console.log_info(f"Module '{module_name}' successfully loaded.")
            except Exception as e:
                console.log_error(f"Failed to load module '{module_name}': {e}.")
                success = False

        if success:
            console.log_success("All modules loaded.")
