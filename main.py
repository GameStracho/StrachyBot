from os import getenv
from typing import List, Optional
from colorama import Fore

import discord
from discord import Color
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

from lib import console, wordle, tic, quote

load_dotenv()
TOKEN: str | None = getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", case_insensitive=True, intents=intents)


if TOKEN is not None:
    bot.run(TOKEN)
else:
    print("ERROR: Could not load discord token.")

@bot.event
async def on_ready() -> None:
    console.log("INFO", (
        f"{Fore.YELLOW}{str(bot.user)}{Fore.WHITE} "
        f"is now online and ready to serve!"))

    synced: List[app_commands.AppCommand] = await bot.tree.sync()
    synced_commands: str = ""
    for command in synced:
        if len(synced_commands):
            synced_commands += f", {command.name}"
        else:
            synced_commands += command.name

    console.log("INFO", (
        f"Slash commands synced: {Fore.YELLOW}{synced_commands}{Fore.WHITE}"))


async def __restrict_command(interaction: discord.Interaction, user_id: int) -> bool:
    if user_id == 217607696361193475:
        return True
    else:
        await interaction.response.send_message(
            ephemeral=True, content="You don't have permissions to use this command.")
    return False


@bot.tree.command(
    name="wordle_play", description="Try to guess a word in 6 tries.")
async def wordle_play(interaction: discord.Interaction):
    await wordle.start(interaction)


@bot.tree.command(name="wordle_guess", description="Guess a word in Wordle.")
async def wordle_guess(interaction: discord.Interaction, word: str):
    if wordle.is_playing(interaction.user.id):
        await wordle.guess(word, interaction)
    else:
        await interaction.response.send_message(
            ephemeral=True, content="You have to start a new game first.")


@bot.tree.command(
    name="tic_tac_toe", description="Challenge someone in Tic-Tac-Toe")
#@app_commands.describe(grid_size="")
@app_commands.choices(grid_size=[
    discord.app_commands.Choice(name="3x3", value=3),
    discord.app_commands.Choice(name="4x4", value=4),
    discord.app_commands.Choice(name="5x5", value=5)
])
async def tic_play(
    interaction: discord.Interaction, opponent: discord.User,
    grid_size: app_commands.Choice[int]):
    user_id: int = interaction.user.id
    if user_id == opponent.id:
        await interaction.response.send_message(
            ephemeral=True,
            content=f"To play singleplayer choose {bot.user.mention if bot.user is not None else ""} as your opponent. - Coming soon")
    else:
        await tic.start(interaction, opponent, grid_size.value)


@bot.tree.command(
    name="quote_guess", description="Try to guess anime by it's quote.")
async def quote_guess(interaction: discord.Interaction):
    await quote.start(interaction)

@bot.tree.command(
    name="announcement", description="Announce messages in chat.")
async def announcement(
        interaction: discord.Interaction,
        title: Optional[str] = "",
        message:  Optional[str] = ""):
    console.log("INFO", ( f"{interaction.user.display_name} used command /announce."))
    
    embed: discord.Embed = discord.Embed(color=Color.yellow())
    if title:
        embed.title = title
    if message:
        embed.description = message
    
    await interaction.response.send_message(embed=embed)
