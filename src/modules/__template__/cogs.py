import discord
from discord import app_commands
from discord.ext import commands, tasks
from typing_extensions import override

from shared import StrachyBot, logger, ui

from .game import Game
from .ui import View


class Cog(commands.Cog):
    _bot: StrachyBot

    def __init__(self, bot: StrachyBot) -> None:
        self._bot = bot

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

            game: Game = Game(player=user)
            await game.start()

            view: View = View(game=game, timeout=15.0)
            embed, icon = view.build_embed()

            logger.info(f"New {game} started by user {user}")
            await interaction.response.send_message(embed=embed, view=view, file=icon)

            # CRITICAL: Save the sent message to the view so the timeout handler can edit it!
            view.message = await interaction.original_response()
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)
