import json
from typing import List

import discord


def __load() -> dict:
    with open("./src/user_data.json", "r", encoding="utf-8") as file:
        stats: dict = json.load(file)
    return stats


def __save(stats: dict) -> None:
    with open("./src/user_data.json", "w", encoding="utf-8") as file:
        json.dump(stats, file, indent=4)


def create(user: discord.User | discord.Member, stats: dict) -> dict:
    print("yep")
    if isinstance(user, discord.User):
        return {} # TODO: resolve later

    user_id: int = user.id
    guild: discord.Guild = user.guild

    if str(guild.id) not in stats:
        stats[str(guild.id)] = {
            "server_name": guild.name
        }
    
    guild_stats: dict = stats[str(guild.id)]

    if str(user_id) not in guild_stats:
        guild_stats[str(user_id)] = {}
    
    if "name" not in guild_stats[str(user_id)]:
        guild_stats[str(user_id)]["name"] = user.name

    stats_names: List[str] = [
        "exp", "mini_games", "cute", "waifu", "who_asked", "who_asked_time"
    ]
    __create_stats(guild_stats[str(user_id)], stats_names)
    return stats


def __create_stats(stats: dict, stats_names: List[str]):
    for stat in stats_names:
        if stat not in stats:
            stats[stat] = {}
            if stat == "mini_games":
                __create_stats(stats[stat], [
                    "wordle", "tic", "quote",
                    "hangman", "anagram", "trivia"
                ])
            elif stat == "anagram":
                __create_stats(stats[stat], [
                    "singleplayer_games", "singleplayer_wins",
                    "multiplayer_games", "multiplayer_wins"
                ])
            elif stat == "trivia":
                __create_stats(stats[stat], [
                    "easy_shown", "easy_correct", "medium_shown",
                    "medium_correct", "hard_shown", "hard_correct"
                ])
            elif stat in ["wordle", "tic", "quote", "hangman"]:
                __create_stats(stats[stat], [
                    "games", "wins"
                ])
            else:
                stats[stat] = 0



def edit(user: discord.User | discord.Member, stat_category: str, stat_name: str, stat_value: int) -> None:
    stats: dict = __load()
    stats = create(user, stats)
    user_stats: dict = {}

    if isinstance(user, discord.Member):
        stats[str(user.guild.id)][str(user.id)]

    if stat_category:
       user_stats["mini_games"][stat_category][stat_name] += stat_value
    else:
        user_stats[stat_name] += stat_value
    __save(stats)
