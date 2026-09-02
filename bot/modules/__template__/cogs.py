import os

import discord
import httpx
from discord import app_commands
from discord.ext import commands, tasks
from typing_extensions import override

from api.modules.__template__.schemas import GameResponse
from shared import StrachyBot, logger, ui

from .ui import View


class Cog(commands.Cog):
    _bot: StrachyBot
    _api_client: httpx.AsyncClient

    def __init__(self, bot: StrachyBot) -> None:
        self._bot = bot

        base_url: str = os.getenv("API_URL", "http://localhost:8000")
        self._api_client = httpx.AsyncClient(base_url=f"{base_url}/games/__template__/")

    @override
    async def cog_load(self) -> None:
        """Called automatically when the cog is loaded."""
        self.weekly_task.start()

    @override
    async def cog_unload(self) -> None:
        """Called automatically when the cog is unloaded."""
        self.weekly_task.stop()

    # Run once a week (every 168 hours)
    @tasks.loop(hours=168)
    async def weekly_task(self) -> None:
        """Called automatically every 7 days."""
        logger.info("Executing weekly task...")

    @weekly_task.before_loop
    async def before_weekly_task(self) -> None:
        """Wait until the bot is fully logged in before running the loop."""
        await self._bot.wait_until_ready()

    @app_commands.command(name="command", description="Description.")
    async def command(
        self,
        interaction: discord.Interaction,
    ) -> None:
        try:
            user = ui.get_user(user=interaction.user)
            logger.debug(f"Command '/command' used by user {user}.")

            response = await self._api_client.post(
                url="start", json={"user_id": interaction.user.id}
            )
            response.raise_for_status()
            game_data: GameResponse = GameResponse.model_validate(response.json())

            view: View = View(
                match_id=game_data.match_id,
                player_id=game_data.player_id,
                status=game_data.status,
                api_client=self._api_client,
                timeout=15.0,
            )
            embed, icon = view.build_embed(player=user)

            logger.info(f"New {game_data} started by user {user}")
            await interaction.response.send_message(embed=embed, view=view, file=icon)

            # CRITICAL: Save the sent message to the view so the timeout handler can edit it!
            view.message = await interaction.original_response()
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)
