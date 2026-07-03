from typing import Optional
import datetime

from shared import console
from shared import messages

import discord
from discord import Color

async def show_info(interaction: discord.Interaction, start_time: datetime.datetime):
    console.log_info(f"/info: User {interaction.user.display_name} used the command.")

    try:
        uptime: datetime.timedelta = discord.utils.utcnow() - start_time

        embed: discord.Embed = discord.Embed(
            color=Color.darker_grey(),
            title="Bot information",
            description="Discord bot with fun mini-games like *Wordle* and *Tic-Tac-Toe*.")
        
        embed.add_field(name="Ping", value=f"{round(interaction.client.latency * 1000)} ms", inline=True)
        embed.add_field(name="Uptime", value=f"{str(uptime).split('.')[0]}", inline=True)

        embed.add_field(name="Version", value="v1.0.3 (02.07.2026)", inline=True)
        embed.add_field(name="Changelog", value=(
            "- Added `/info` command"
            "\n- Fixed errors in `/announcement` command"
            "\n- Added error handlers"
        ), inline=False)
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await messages.handle_error(e, interaction)


async def announce(interaction: discord.Interaction, title: Optional[str], message: Optional[str]):
    console.log_info(f"/info: User {interaction.user.display_name} passed title '{title}' and '{message}'.")
    
    try:
        embed: discord.Embed = discord.Embed(color=Color.yellow())
        if title:
            embed.title = title
        if message:
            embed.description = message

        icon: discord.File = discord.File(
        "./src/modules/utils/announcement.png", filename="announcement.png")
        embed.set_thumbnail(url="attachment://announcement.png")
        
        await interaction.response.send_message(embed=embed, file=icon)
    except Exception as e:
        await messages.handle_error(e, interaction)