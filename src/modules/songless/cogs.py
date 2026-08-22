from typing import override

import discord
from discord import app_commands
from discord.ext import commands, tasks

from shared import StrachyBot, ui, logger

PLAYLISTS: list[str] = []

class SonglessCog(commands.Cog):
    _bot: StrachyBot

    def __init__(self, bot: StrachyBot) -> None:
        self._bot = bot

    @override
    async def cog_load(self) -> None:
        """Called automatically when the cog is loaded."""
        self.update_songs.start()

    @override
    async def cog_unload(self) -> None:
        """Called automatically when the cog is unloaded."""
        self.update_songs.cancel()

    # Run once a week (every 168 hours)
    @tasks.loop(minutes=1)
    async def update_songs(self) -> None:
        """Fetch PLAYLISTS and save new songs into the database."""
        print("Adding songs...")

    @update_songs.before_loop
    async def before_update_songs(self) -> None:
        """Wait until the bot is fully logged in before running the loop."""
        await self._bot.wait_until_ready()
