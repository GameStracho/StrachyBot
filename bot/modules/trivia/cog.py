import json
import os

import discord
import httpx
from discord import app_commands
from discord.ext import commands

from bot.bot import StrachyBot
from shared import logger, ui
from shared.modules.trivia import ETriviaCategory, ETriviaDifficulty, StartRequest, TriviaResponse

from .ui import TriviaView


class TriviaCog(commands.Cog):
    _bot: StrachyBot
    _api_client: httpx.AsyncClient

    def __init__(self, bot: StrachyBot) -> None:
        self._bot = bot

        base_url: str = os.getenv("API_URL", "http://localhost:8000")
        self._api_client = httpx.AsyncClient(base_url=f"{base_url}/games/trivia/")

    @app_commands.command(
        name="trivia", description="Try to answer a quiz question by selecting 1 of 4 answers."
    )
    async def trivia(
        self,
        interaction: discord.Interaction,
        category: ETriviaCategory = ETriviaCategory.ANY,
        difficulty: ETriviaDifficulty = ETriviaDifficulty.ANY,
    ) -> None:
        try:
            # Tells Discord to display "Thinking..." and extends time limit to 15 mins
            await interaction.response.defer()
            user = ui.get_user(user=interaction.user)
            logger.debug(f"Command '/trivia' used by user {user}.")

            request = StartRequest(
                user_id=interaction.user.id, category=category, difficulty=difficulty
            )
            response = await self._api_client.post(
                url="start",
                json=json.loads(request.model_dump_json()),
            )

            response.raise_for_status()
            game_data: TriviaResponse = TriviaResponse.model_validate(response.json())

            view: TriviaView = TriviaView(
                game_data=game_data,
                api_client=self._api_client,
                timeout=60.0,
            )
            embed, icon = view.build_embed(player=user)

            logger.info(f"New {game_data} started by user {user}.")

            # CRITICAL: Save the sent message to the view so the timeout handler can edit it!
            await interaction.followup.send(embed=embed, view=view, file=icon)
            view.message = await interaction.original_response()
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)
