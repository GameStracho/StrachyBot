import os
from typing import List, Optional
from colorama import Fore

import discord
from discord import Color
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

from modules import console

load_dotenv()
TOKEN: str | None = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", case_insensitive=True, intents=intents)


if TOKEN is not None:
    bot.run(TOKEN)
else:
    print("ERROR: Could not load discord token.")


async def load_cogs() -> None:
    """Load all cogs from the modules directory."""
    cogs_dir = os.path.join(os.path.dirname(__file__), "modules")
    
    for module_name in os.listdir(cogs_dir):
        module_path = os.path.join(cogs_dir, module_name)
        
        # Skip non-directories and utility modules
        if not os.path.isdir(module_path) or module_name.startswith("_"):
            continue
        
        # Skip if cogs.py does not exist in the module
        cogs_file = os.path.join(module_path, "cogs.py")
        if not os.path.exists(cogs_file):
            continue

        try:
            await bot.load_extension(f"modules.{module_name}.cogs")
            console.log("INFO", f"Loaded cog: {module_name}")
        except Exception as e:
            console.log("ERROR", f"Failed to load cog {module_name}: {e}")


@bot.event
async def setup_hook() -> None:
    """Called before the bot logs in."""
    await load_cogs()


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
