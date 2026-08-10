import datetime

import discord
from discord import app_commands
from discord.ext import commands

from shared import console, messages
from shared.bot import StrachyBot

from .helpers import parse_changelog


class UtilsCog(commands.Cog):
    def __init__(self, bot: StrachyBot) -> None:
        self.bot = bot

    @app_commands.command(name="info", description="Show important information about the bot")
    async def info(self, interaction: discord.Interaction) -> None:
        console.log_info(f"/info: User {interaction.user.display_name} used the command.")

        try:
            uptime: datetime.timedelta = discord.utils.utcnow() - self.bot.start_time

            embed: discord.Embed = discord.Embed(
                color=discord.Color.blue(),
                title="StrachyBot 🤖",
                description="Discord bot with fun mini-games like *Wordle* and *Tic-Tac-Toe*.",
            )

            embed.add_field(
                name="Ping", value=f"{round(interaction.client.latency * 1000)} ms", inline=True
            )
            embed.add_field(name="Uptime", value=f"{str(uptime).split('.')[0]}", inline=True)

            sections: list[tuple[str, str]] = parse_changelog()

            for section_name, section_content in sections:
                embed.add_field(name=section_name, value=section_content, inline=False)

            icon: discord.File = discord.File("./src/modules/utils/info.png", filename="info.png")
            embed.set_thumbnail(url="attachment://info.png")

            await interaction.response.send_message(embed=embed, file=icon)
        except Exception:
            await messages.handle_error("/info", interaction)

    @app_commands.command(name="announcement", description="Make announcements in chat.")
    async def announcement(
        self, interaction: discord.Interaction, title: str | None = "", message: str | None = ""
    ) -> None:
        console.log_info(
            f"/announcement: User {interaction.user.display_name} "
            f"passed title '{title}' and '{message}'."
        )

        try:
            embed: discord.Embed = discord.Embed(color=discord.Color.yellow())
            if title:
                embed.title = title
            if message:
                embed.description = message

            icon: discord.File = discord.File(
                "./src/modules/utils/announcement.png", filename="announcement.png"
            )
            embed.set_thumbnail(url="attachment://announcement.png")

            await interaction.response.send_message(embed=embed, file=icon)
        except Exception:
            await messages.handle_error("/announcement", interaction)
