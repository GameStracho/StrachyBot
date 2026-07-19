import traceback

import discord
from discord import Color

from shared import console

async def handle_error(command: str, interaction: discord.Interaction, use_followup: bool = False) -> None:
    """
    Print error message with details to console and send generic message to user.
    IMPORTANT: only call from an except block!
    """
    console.log_error(f"{command}: An unexpected error occurred for user {interaction.user.display_name}: \n{traceback.format_exc()}")

    embed: discord.Embed = discord.Embed(color=Color.red())
    embed.title = "Error"
    embed.description = "An unexpected error occurred. Try again later."

    icon: discord.File = discord.File(
        "./src/images/error.png", filename="error.png")
    embed.set_thumbnail(url="attachment://error.png")

    if use_followup:
        await interaction.followup.send(embed=embed, file=icon, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, file=icon, ephemeral=True)
