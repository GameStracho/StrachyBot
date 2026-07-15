from typing import List
import random

import discord
from discord.ext import commands
from discord import app_commands

from shared.bot import StrachyBot
from shared import console, messages
from .view import TriviaView

class TriviaCog(commands.Cog):
    def __init__(self, bot: StrachyBot) -> None:
        self.bot = bot

    @app_commands.command(
        name="trivia", description="Try to answer a question by selecting 1 of 4 answers.")
    async def trivia(self, interaction: discord.Interaction):
        try:
            console.log_info(f"/trivia: Command used by user {interaction.user.display_name} ({interaction.user.id})")
            
            options: List[str] = []
            correct_answer = "Option 1"

            for i in range(4):
                options.append(f"Option {i}")

            random.shuffle(options)

            game_id: int = 1

            view: TriviaView = TriviaView(game=game_id, options=options, correct_answer=correct_answer)

            embed = discord.Embed(color=discord.Color.green(), title="Trivia", description="Some Question?")

            console.log_info(f"/trivia: User {interaction.user.display_name} ({interaction.user.id}) started a new game ({game_id}). Correct answer is '{correct_answer}'.")          
            # CRITICAL: Save the sent message reference to the view so the timeout handler can edit it!
            await interaction.response.send_message(embed=embed, view=view)
            view.message = await interaction.original_response()
        except Exception:
            await messages.handle_error("/trivia", interaction)