import discord
from discord import app_commands
from discord.ext import commands

from shared import bot, console, messages

from .game import WordleGame
from .ui import WordleView


class WordleCog(commands.Cog):
    def __init__(self, bot: bot.StrachyBot) -> None:
        self.bot = bot

    @app_commands.command(name="wordle", description="Try to guess a 5-letter word in 6 tries.")
    async def wordle(self, interaction: discord.Interaction) -> None:
        try:
            console.log_debug(f"/wordle: Command used by user {interaction.user.display_name} ({interaction.user.id})")

            game: WordleGame = WordleGame(player_id=interaction.user.id)
            await game.connect_database(bot=self.bot)
            view: WordleView = WordleView(game=game, timeout=300.0)
            embed, icon = view.build_embed(interaction.user)

            console.log_info(f"/wordle: User {interaction.user.display_name} ({interaction.user.id}) started a new {game}.")
            
            # CRITICAL: Save the sent message reference to the view so the timeout handler can edit it!
            await interaction.response.send_message(embed=embed, view=view, file=icon)
            view.message = await interaction.original_response()
        except Exception:
            await messages.handle_error(command="/wordle", interaction=interaction, use_followup=False)
