import discord
from discord.ext import commands
from discord import app_commands

from modules.tic import logic


class TicCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="tic_tac_toe", description="Challenge someone in Tic-Tac-Toe")
    @app_commands.choices(grid_size=[
        discord.app_commands.Choice(name="3x3", value=3),
        discord.app_commands.Choice(name="4x4", value=4),
        discord.app_commands.Choice(name="5x5", value=5)
    ])
    async def tic_play(
        self, interaction: discord.Interaction, opponent: discord.User,
        grid_size: app_commands.Choice[int]):
        user_id: int = interaction.user.id
        mention: str = self.bot.user.mention if self.bot.user is not None else ""
        if user_id == opponent.id:
            await interaction.response.send_message(
                ephemeral=True,
                content=f"To play singleplayer choose {mention} as your opponent. - Coming soon")
        else:
            await logic.start(interaction, opponent, grid_size.value)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TicCog(bot))
