from modules import console

import discord
from discord import Color

async def handle_error(ex: Exception, interaction: discord.Interaction):
    console.log_error(f"/info: An unexpected error occurred for user {interaction.user.display_name}: \n{ex}")

    embed: discord.Embed = discord.Embed(color=Color.red())
    embed.title = "Error"
    embed.description = "An unexpected error occurred. Try again later."
    await interaction.response.send_message(embed=embed, ephemeral=True)
