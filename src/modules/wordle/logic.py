import json
import random
import re
from typing import Dict, List

import discord
from discord import Color

from modules import stats
from shared import console


games: Dict[int, dict] = {}
words: List[str] = []
emojis: dict = {}

with open("./src/wordle-words.txt", "r", encoding="utf-8") as file:
    words = file.readlines()

with open("./src/emojis.json", "r", encoding="utf-8") as file:
    emojis = json.load(file)


def is_playing(user_id: int):
    return user_id in games


async def start(interaction: discord.Interaction) -> None:
    user: discord.User | discord.Member = interaction.user
    msg: str = "⬜ ⬜ ⬜ ⬜ ⬜"
    embed = discord.Embed(color=Color.blue(), title="Wordle", description=msg)
    embed.set_author(name=user.display_name, icon_url=user.display_avatar)

    icon: discord.File = discord.File(
        "./src/modules/wordle/icon.png", filename="wordle.png")
    embed.set_thumbnail(url="attachment://wordle.png")

    searched_word: str = random.choice(words).split("\n")[0]

    game_info: dict = {
        "interaction": interaction,
        "embed": embed,
        "lives": 6,
        "searched_word": searched_word,
        "guessed_words": [],
        "msg": msg
    }
    games[user.id] = game_info

    console.log_info((
        "WORDLE"
        f"{user.display_name} has started a new game. "
        f"The word is: {searched_word}."))

    stats.edit(user, "wordle", "games", 1)
    await interaction.response.send_message(file=icon, embed=embed)


async def guess(word: str, interaction: discord.Interaction):
    user_id: int = interaction.user.id
    game_info: dict = games[user_id]
    embed: discord.Embed = game_info["embed"]
    info_line: str = ""
    msg: str = game_info["msg"]
    word = word.lower()

    if len(word) > 5:
        info_line = "Entered word is too long!"
    elif len(word) < 5:
        info_line = "Entered word is too short!"
    elif not re.match(r"^[A-Za-z]*$", word) or word + "\n" not in words:
        info_line = "Entered invalid word!"
    elif word in game_info["guessed_words"]:
        info_line = "You already guessed that!"
    else:
        games[user_id]["guessed_words"].append(word)

        if game_info["lives"] == 6:
            msg = ""
        else:
            msg += "\n\n"

        square_line: str = "\n"
        searched_word = game_info["searched_word"]
        for i in range(len(word)):
            msg += f" {emojis[word[i]]} "

            if word[i] == searched_word[i]:
                square_line += " 🟩 "
            elif word[i] in searched_word:
                if (word[i+1:].count(word[i]) == searched_word.count(word[i]) or
                    word[:i].count(word[i]) == searched_word.count(word[i])):
                        square_line += " 🟥 "
                else:
                    square_line += " 🟧 "
            else:
                square_line += " 🟥 "
        msg += square_line

        games[user_id]["lives"] -= 1
        games[user_id]["msg"] = msg
        if word == searched_word:
            games[user_id]["lives"] = 0
            info_line = "You Won! *+25 xp*"
            embed.color = Color.green()
            stats.edit(interaction.user, "wordle", "wins", 1)
            stats.edit(interaction.user, "", "exp", 25)
        elif games[user_id]["lives"] == 0:
            info_line = (f"You Lost. The correct word was: {searched_word}. "
                         f"*+5 xp*")
            embed.color = Color.red()
            stats.edit(interaction.user, "", "exp", 5)
        else:
            info_line = "Valid guess."


    embed.description = msg + "\n\n" + info_line
    await __respond(interaction)

async def __respond(interaction: discord.Interaction):
    user_id: int = interaction.user.id
    if user_id in games:
        game_info: dict = games[user_id]
        old_interaction: discord.Interaction = game_info["interaction"]
        embed: discord.Embed = game_info["embed"]
        icon: discord.File = discord.File(
            "./src/images/icon_wordle.png", filename="icon_wordle.png")
        embed.set_thumbnail(url="attachment://icon_wordle.png")
        await interaction.response.send_message(file=icon, embed=embed)
        game_info["interaction"] = interaction
        await old_interaction.delete_original_response()

        if game_info["lives"] == 0:
            games.pop(user_id)
