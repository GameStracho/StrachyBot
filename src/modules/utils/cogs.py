from typing import Optional, List, Tuple
import datetime

import discord
from discord.ext import commands
from discord import app_commands

from shared.bot import StrachyBot
from shared import console, messages
from .helpers import parse_changelog

class UtilsCog(commands.Cog):
    def __init__(self, bot: StrachyBot) -> None:
        self.bot = bot

    @app_commands.command(name="info", description="Show important information about the bot")
    async def info(
        self,
        interaction: discord.Interaction) -> None:
        console.log_info(f"/info: User {interaction.user.display_name} used the command.")

        try:
            uptime: datetime.timedelta = discord.utils.utcnow() - self.bot.start_time

            embed: discord.Embed = discord.Embed(
                color=discord.Color.blue(),
                title="Bot information",
                description="Discord bot with fun mini-games like *Wordle* and *Tic-Tac-Toe*."
            )
            
            embed.add_field(name="Ping", value=f"{round(interaction.client.latency * 1000)} ms", inline=True)
            embed.add_field(name="Uptime", value=f"{str(uptime).split('.')[0]}", inline=True)

            sections: List[Tuple[str, str]] = parse_changelog()

            for section_name, section_content in sections:
                embed.add_field(name=section_name, value=section_content, inline=False)

            icon: discord.File = discord.File(
            "./src/modules/utils/info.png", filename="info.png")
            embed.set_thumbnail(url="attachment://info.png")
            
            await interaction.response.send_message(embed=embed, file=icon)
        except Exception as e:
            await messages.handle_error(e, interaction)


    @app_commands.command(name="announcement", description="Make announcements in chat.")
    async def announcement(
        self,
        interaction: discord.Interaction,
        title: Optional[str] = "",
        message:  Optional[str] = "") -> None:
        console.log_info(f"/info: User {interaction.user.display_name} passed title '{title}' and '{message}'.")
    
        try:
            embed: discord.Embed = discord.Embed(color=discord.Color.yellow())
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
