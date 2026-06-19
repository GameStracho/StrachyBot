from modules import console
from typing import Optional

import discord
from discord import Color

async def announce(interaction: discord.Interaction, title: Optional[str], message: Optional[str]):
    console.log_info(f"{interaction.user.display_name} used command /announce.")
    
    embed: discord.Embed = discord.Embed(color=Color.yellow())
    if title:
        embed.title = title
    if message:
        embed.description = message
    
    await interaction.response.send_message(embed=embed)