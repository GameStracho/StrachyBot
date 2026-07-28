import discord
from discord.ext import commands
from discord import app_commands

from shared import console, bot, messages, helpers
from .ui import TicTacToeView, get_player_emojis, PLAYER_COLOR
from .game import TicTacToeGame

class TicCog(commands.Cog):
    def __init__(self, bot: bot.StrachyBot) -> None:
        self.bot = bot


    @app_commands.command(
        name="tic-tac-toe", description="Challenge someone in a 1v1 Tic-Tac-Toe match")
    @app_commands.choices(grid_size=[
        discord.app_commands.Choice(name="3x3", value=3),
        discord.app_commands.Choice(name="4x4", value=4),
        discord.app_commands.Choice(name="5x5", value=5)
    ])
    async def tic_tac_toe(self, interaction: discord.Interaction, opponent: discord.User,
                          grid_size: app_commands.Choice[int]) -> None:
        try:
            console.log_debug(f"/tic-tac-toe: Command used by user {interaction.user.display_name} ({interaction.user.id})")

            player: discord.User

            if isinstance(interaction.user, discord.User):
                player = interaction.user
            else:
                temp_player: discord.User | None = await self.bot.fetch_user(interaction.user.id)
                assert temp_player
                player = temp_player

            game: TicTacToeGame = TicTacToeGame(player=player, opponent=opponent, grid_size=grid_size.value)
            view: TicTacToeView = TicTacToeView(game=game, timeout=15.0)

            player_emoji, opponent_emoji = get_player_emojis()

            embed = discord.Embed(color=PLAYER_COLOR, title="Tic-Tac-Toe")
            embed.add_field(name="Players", value=f"{player_emoji} {game.get_player().mention}\n{opponent_emoji} {game.get_opponent().mention}", inline=False)

            embed.add_field(name="Status", value=f"It's {player_emoji} {game.get_player().mention}'s turn.", inline=False)
            embed.add_field(name="Timeout", value=view.get_timeout_timestamp(), inline=False)

            icon, icon_url = helpers.load_attachment(path=__file__, filename="icon.png")
            embed.set_thumbnail(url=icon_url)

            console.log_info(f"/tic-tac-toe: User {interaction.user.display_name} ({interaction.user.id}) started a new {game}.")
            # CRITICAL: Save the sent message reference to the view so the timeout handler can edit it!
            await interaction.response.send_message(embed=embed, view=view, file=icon)
            view.message = await interaction.original_response()
        except Exception:
            await messages.handle_error(command="/tic-tac-toe", interaction=interaction, use_followup=False)
