import json
from typing import List

import discord


def __load() -> dict:
    with open("./src/stats.json", "r", encoding="utf-8") as file:
        stats: dict = json.load(file)
    return stats


def __save(stats: dict) -> None:
    with open("./src/stats.json", "w", encoding="utf-8") as file:
        json.dump(stats, file, indent=4)


def create(user: discord.Member, stats: dict) -> dict:
    user_id: int = user.id
    if str(user_id) not in stats:
        stats[str(user_id)] = {}

    stats_names: List[str] = [
        "exp", "wordle_games", "wordle_wins", "tic_games",
        "tic_wins", "quote_games", "quote_wins"]
    for stat in stats_names:
        if stat not in stats[str(user_id)]:
            stats[str(user_id)][stat] = 0
    if "name" not in stats[str(user_id)]:
        stats[str(user_id)]["name"] = user.name
    return stats


def edit(user: discord.User, stat_name: str, stat_value: int) -> None:
    stats: dict = __load()
    stats = create(user, stats)
    stats[str(user.id)][stat_name] += stat_value
    __save(stats)
