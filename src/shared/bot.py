import os
from typing import List
from colorama import Fore

import discord
from discord.ext import commands
from discord import app_commands

from modules import console

class StrachyBot(commands.Bot):
    def __init__(self):
        # Setup intents
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix="!", case_insensitive=True, intents=intents)

        self.start_time = discord.utils.utcnow()


    async def setup_hook(self) -> None:
        """Called before the bot logs in."""
        await self.__load_cogs()


    async def on_ready(self) -> None:
        """Called when the bot starts."""

        console.log_info(console.highlight(Fore.YELLOW, str(self.user)) + " is now online and ready to serve!")

        synced: List[app_commands.AppCommand] = await self.tree.sync()
        synced_commands: str = ""
        for command in synced:
            if len(synced_commands):
                synced_commands += f", {command.name}"
            else:
                synced_commands += command.name

        console.log_info(f"Slash commands synced: {console.highlight(Fore.YELLOW, synced_commands)}")


    async def __load_cogs(self) -> None:
        """Load all cogs from the modules directory."""
        cogs_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "modules"))
        
        for module_name in os.listdir(cogs_dir):
            module_path = os.path.join(cogs_dir, module_name)
            
            # Skip non-directories and utility modules
            if not os.path.isdir(module_path) or module_name.startswith("_"):
                continue
            
            # Skip if cogs.py does not exist in the module
            cogs_file = os.path.join(module_path, "cogs.py")
            if not os.path.exists(cogs_file):
                continue

            try:
                await self.load_extension(f"modules.{module_name}.cogs")
                console.log_info(f"Loaded cog: {module_name}")
            except Exception as e:
                console.log_error(f"Failed to load cog {module_name}: {e}")
