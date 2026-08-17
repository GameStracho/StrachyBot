import datetime

import discord
from discord import app_commands
from discord.ext import commands

from shared import StrachyBot, logger, ui

from .helpers import parse_changelog


class UtilsCog(commands.Cog):
    def __init__(self, bot: StrachyBot) -> None:
        self.bot = bot

    @app_commands.command(name="info", description="Show important information about the bot")
    async def info(self, interaction: discord.Interaction) -> None:
        logger.info(f"/info: User {interaction.user.display_name} used the command.")

        try:
            uptime: datetime.timedelta = discord.utils.utcnow() - self.bot.start_time
            description: str = (
                "Discord bot with fun mini-games like *Trivia*, *Wordle* and *Tic-Tac-Toe*."
            )

            embed: discord.Embed = discord.Embed(
                color=discord.Color.teal(),
                title="StrachyBot 🤖",
                description=description,
            )

            embed.add_field(
                name="Ping", value=f"{round(interaction.client.latency * 1000)} ms", inline=True
            )
            embed.add_field(name="Uptime", value=f"{str(uptime).split('.')[0]}", inline=True)

            sections: list[tuple[str, str]] = parse_changelog()

            for section_name, section_content in sections:
                embed.add_field(name=section_name, value=section_content, inline=False)

            icon, icon_url = ui.load_attachment(path=__file__, filename="icon.png")
            embed.set_thumbnail(url=icon_url)

            await interaction.response.send_message(embed=embed, file=icon)
        except Exception:
            await ui.handle_error("/info", interaction)
