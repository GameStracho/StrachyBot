from shared import console

import discord
from discord import Color

async def handle_error(ex: Exception, interaction: discord.Interaction):
    console.log_error(f"An unexpected error occurred for user {interaction.user.display_name}: \n{ex}")

    embed: discord.Embed = discord.Embed(color=Color.red())
    embed.title = "Error"
    embed.description = "An unexpected error occurred. Try again later."

    icon: discord.File = discord.File(
        "./src/images/error.png", filename="error.png")
    embed.set_thumbnail(url="attachment://error.png")

    await interaction.response.send_message(embed=embed, file=icon, ephemeral=True)
