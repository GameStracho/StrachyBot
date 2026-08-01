import discord
from discord import app_commands
from discord.ext import commands

from modules.wordle import logic
from shared import bot, console, helpers, messages, ui

from .game import WordleGame
from .ui import WordleView


class WordleCog(commands.Cog):
    def __init__(self, bot: bot.StrachyBot) -> None:
        self.bot = bot

    @app_commands.command(
        name="wordle_play", description="Try to guess a word in 6 tries.")
    async def wordle_play(self, interaction: discord.Interaction) -> None:
        await logic.start(interaction)

    @app_commands.command(name="wordle_guess", description="Guess a word in Wordle.")
    async def wordle_guess(self, interaction: discord.Interaction, word: str) -> None:
        if logic.is_playing(interaction.user.id):
            await logic.guess(word, interaction)
        else:
            await interaction.response.send_message(
                ephemeral=True, content="You have to start a new game first.")

    @app_commands.command(name="wordle", description="Try to guess a 5-letter word in 6 tries.")
    async def wordle(self, interaction: discord.Interaction) -> None:
        try:
            console.log_debug(f"/wordle: Command used by user {interaction.user.display_name} ({interaction.user.id})")

            game: WordleGame = WordleGame(player_id=interaction.user.id)

            view: WordleView = WordleView(game=game, timeout=180.0)
            embed: discord.Embed = discord.Embed(title="Wordle", color=discord.Color.blue())
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar)

            empty_word: str = ui.EMOJIS["wordle_empty_letter"]

            for i in range(4):
                empty_word += " " + ui.EMOJIS["wordle_empty_letter"]

            for i in range(6):
                embed.add_field(name="Guess #" + str(i + 1), value=empty_word, inline=False)

            embed.add_field(name="Status", value="Game started. You can start guessing.", inline=False)

            icon, icon_url = helpers.load_attachment(path=__file__, filename="icon.png")
            embed.set_thumbnail(url=icon_url)

            console.log_info(f"/wordle: User {interaction.user.display_name} ({interaction.user.id}) started a new {game}.")
            
            # CRITICAL: Save the sent message reference to the view so the timeout handler can edit it!
            await interaction.response.send_message(embed=embed, view=view, file=icon)
            view.message = await interaction.original_response()
        except Exception:
            await messages.handle_error(command="/wordle", interaction=interaction, use_followup=False)
