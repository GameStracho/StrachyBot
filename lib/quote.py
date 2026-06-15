import random
from typing import Dict, List
import discord
from discord import Color
import requests

from lib import console, stats


class QuoteGuessButtons(discord.ui.View):
    def __init__(self, user_id: int) -> None:
        super().__init__(timeout=None)
        self.game_id = user_id

        labels: List[str] = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]

        for i in range(len(labels)):
            button: discord.ui.Button = discord.ui.Button(
                custom_id=str(i), label=labels[i], row=0)
            button.callback = self.button_callback
            self.add_item(button)
    
    async def button_callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
               ephemeral=True, content="responding...", delete_after=0)
        await guess(
                interaction.user, self.game_id,
                int(interaction.data["custom_id"]))


games: Dict[int, dict] = {}


async def start(interaction: discord.Interaction) -> None:
    quotes: dict = requests.get(
        "https://animechan.vercel.app/api/quotes/").json()

    answer: int = random.randint(0, 3)

    choices: List[str] = [
        f"{quotes[0]['anime']} - {quotes[0]['character']}",
        f"{quotes[1]['anime']} - {quotes[1]['character']}",
        f"{quotes[2]['anime']} - {quotes[2]['character']}",
        f"{quotes[3]['anime']} - {quotes[3]['character']}"
    ]

    msg: str = (
        f"From which anime is this quote?\n\n"
        f"`{quotes[answer]['quote']}`\n"
    )

    user: discord.User = interaction.user

    embed = discord.Embed(
        color=Color.blue(), title="Quote Guess", description=msg)
    embed.set_author(name=user.display_name, icon_url=user.display_avatar)

    icon_url: str = requests.get(
        "https://api.waifu.pics/sfw/waifu").json()["url"]
    embed.set_thumbnail(url=icon_url)

    game_info: dict = {
        "interaction": interaction,
        "embed": embed,
        "msg": msg,
        "choices": choices,
        "answer": answer
    }
    games[user.id] = game_info

    msg += (
        f"\n1️⃣ {choices[0]}"
        f"\n2️⃣ {choices[1]}"
        f"\n3️⃣ {choices[2]}"
        f"\n4️⃣ {choices[3]}"
    )

    console.log("QUOTE", (
        f"{user.display_name} has started a new game. "
        f"The correct answer is {answer}."))

    embed.description = msg
    stats.edit(user, "quote", "games", 1)
    await interaction.response.send_message(
        embed=embed, view=QuoteGuessButtons(user.id))


async def guess(user: discord.User, game_id: int, choice: int):
    user_id: int = user.id
    if user_id in games and user_id == game_id:
        game_info: dict = games[user_id]
        embed: discord.Embed = game_info["embed"]
        msg: str = game_info["msg"]

        choices: List[str] = game_info["choices"]
        for i in range(len(choices)):
            if i == game_info["answer"]:
                msg += f"\n✅{choices[i]}"
            elif i == choice:
                msg += f"\n🔴{choices[i]}"
            else:
                msg += f"\n❌{choices[i]}"

        if choice == game_info["answer"]:
            game_info["embed"].color = Color.green()
            stats.edit(user, "quote", "wins", 1)
            stats.edit(user, "", "exp", 5)
            msg += "\n\nCorrect answer! *+5 xp*"
        else:
            game_info["embed"].color = Color.red()
            msg += "\n\nWrong answer."
            games.pop(user_id)

        interaction: discord.Interaction = game_info["interaction"]
        embed.description = msg
        await interaction.edit_original_response(embed=embed, view=None)
