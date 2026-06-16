from typing import Dict, List
from math import sqrt

import discord
from discord import Color

from lib import console, stats


class TicTacToeButtons(discord.ui.View):
    def __init__(self, game_id: int, grid_size: int) -> None:
        super().__init__(timeout=None)
        self.game_id = game_id

        
        for i in range(grid_size):
            for j in range(grid_size):
                button: discord.ui.Button = discord.ui.Button(
                    custom_id=str((i * grid_size) + j), label="\u1CBC", row=i)
                #button.callback = self.button_callback
                self.add_item(button)

    async def button_callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
               ephemeral=True, content="responding...", delete_after=0)
        # TODO: resolve type issues
        #await button_pressed(
        #    self.game_id, int(interaction.data["custom_id"]),
        #    interaction.user.id)


games: Dict[int, dict] = {}


async def start(
        interaction: discord.Interaction, opponent: discord.User, grid_size: int) -> None:
    user: discord.User | discord.Member = interaction.user
    msg: str = f"🟣 - {user.mention}\n🟠 - {opponent.mention}"
    embed = discord.Embed(
        color=Color.purple(), title="Tic-Tac-Toe", description=msg)

    icon: discord.File = discord.File(
        "./src/images/icon_tic.png", filename="icon_tic.png")
    embed.set_thumbnail(url="attachment://icon_tic.png")

    if embed.description is None:
        embed.description = ""

    embed.description += f"\n\nIt's {user.mention}'s turn."

    view: discord.ui.View = TicTacToeButtons(user.id, grid_size)

    game_info: dict = {
        "interaction": interaction,
        "users": [user, opponent],
        "embed": embed,
        "view": view,
        "turn": 0,
        "msg": msg
    }
    
    if user.id in games:
        await __remove_buttons(user.id)

    games[user.id] = game_info

    console.log("TIC", (
        f"{interaction.user.display_name} has started a new game "
        f"against {opponent.display_name}."))

    stats.edit(user, "tic", "games", 1)
    stats.edit(opponent, "tic", "games", 1)
    await interaction.response.send_message(
        file=icon, embed=embed, view=view)


async def button_pressed(game_id: int, button_num: int, user_id: int) -> None:
    game_info: dict = games[game_id]
    embed: discord.Embed = game_info["embed"]
    
    if game_info["users"][game_info["turn"]].id == user_id:
        if change_button_label(game_id, button_num):
            if __check_end(game_id):
                await __remove_buttons(game_id)
                games.pop(game_id)
            else:
                __switch_turns(game_id)
                interaction: discord.Interaction = game_info["interaction"]
                view: discord.ui.View = game_info["view"]
                await interaction.edit_original_response(embed=embed, view=view)


def change_button_label(game_id: int, button_num: int) -> bool:
    game_info: dict = games[game_id]
    view: discord.ui.View = game_info["view"]
    btn = view.children[button_num]
    if not isinstance(btn, discord.ui.Button):
        return False
    if btn.label == "\u1CBC":
        if game_info["turn"]:
            btn.label = "🟠"
        else:
            btn.label = "🟣"
        return True
    return False


def __check_end(game_id: int) -> bool:
    game_info: dict = games[game_id]
    view: discord.ui.View = game_info["view"]
    embed: discord.Embed = game_info["embed"]

    symbol: str = ""
    if game_info["turn"]:
            symbol = "🟠"
    else:
        symbol = "🟣"
    
    if (__check_rows(view, symbol) or
        __check_columns(view, symbol) or 
        __check_diagonals(view, symbol)):
        user = game_info['users'][game_info['turn']]
        embed.description = f"{game_info['msg']}\n\n{user.mention} won! *+15 xp for winner*"
        stats.edit(user, "tic", "wins", 1)
        stats.edit(user, "", "exp", 15)
        return True

    for button in view.children:
        if not isinstance(button, discord.ui.Button):
            continue
        if button.label == "\u1CBC":
            return False
    embed.description = f"{game_info['msg']}\n\nGame ended in a draw. *+5 xp for both*"
    stats.edit(game_info['users'][0], "", "exp", 5)
    stats.edit(game_info['users'][1], "", "exp", 5)
    embed.color = Color.lighter_grey()
    return True


def __check_rows(view: discord.ui.View, symbol: str) -> bool:
    rows_num: int = int(sqrt(len(view.children)))
    for i in range(rows_num):
        for j in range(rows_num - 2):
            #print(f"rows: {(i * rows_num) + j}, {(i * rows_num) + j + 1}, {(i * rows_num) + j + 2}")
            a = view.children[(i * rows_num) + j]
            b = view.children[(i * rows_num) + j + 1]
            c = view.children[(i * rows_num) + j + 2]
            if not (isinstance(a, discord.ui.Button) and isinstance(b, discord.ui.Button) and isinstance(c, discord.ui.Button)):
                continue
            if (a.label == symbol and b.label == symbol and c.label == symbol):
                return True
    return False


def __check_columns(view: discord.ui.View, symbol: str) -> bool:
    columns_num: int = int(sqrt(len(view.children)))
    for i in range(columns_num):
        for j in range(columns_num - 2):
            #print(f"columns: {i + (j * columns_num)}, {i + ((j + 1) * columns_num)}, {i + ((j + 2) * columns_num)}")
            a = view.children[i + (j * columns_num)]
            b = view.children[i + ((j + 1) * columns_num)]
            c = view.children[i + ((j + 2) * columns_num)]
            if not (isinstance(a, discord.ui.Button) and isinstance(b, discord.ui.Button) and isinstance(c, discord.ui.Button)):
                continue
            if (a.label == symbol and b.label == symbol and c.label == symbol):
                return True
    return False


def __check_diagonals(view: discord.ui.View, symbol: str) -> bool:
    diagonals_num: int = int(sqrt(len(view.children)))

    starting_points: List[List[int]] = [[], []]

    for i in range(diagonals_num - 2):
        for j in range(diagonals_num - 2):
            starting_points[0].append((i*diagonals_num) + j + 2)
            starting_points[1].append((i*diagonals_num) + j)
    
    for i in range(2):
        step: int = (diagonals_num - 1) + (i * 2)
        #print(f"step: {step}")
        for starting_point in starting_points[i]:
            a = view.children[starting_point]
            b = view.children[starting_point + step]
            c = view.children[starting_point + 2 * step]
            if not (isinstance(a, discord.ui.Button) and isinstance(b, discord.ui.Button) and isinstance(c, discord.ui.Button)):
                continue
            if (a.label == symbol and b.label == symbol and c.label == symbol):
                return True
    return False


def __switch_turns(game_id: int) -> None:
    game_info: dict = games[game_id]
    embed: discord.Embed = game_info["embed"]
    if game_info["turn"]:
        game_info["turn"] = 0
        embed.color = Color.purple()
    else:
        game_info["turn"] = 1
        embed.color = Color.orange()
    embed.description = (
        f"{game_info['msg']}"
        f"\n\nIt's {game_info['users'][game_info['turn']].mention}'s turn.")


async def __remove_buttons(game_id: int) -> None:
    game_info: dict = games[game_id]
    view: discord.ui.View = game_info["view"]
    embed: discord.Embed = game_info["embed"]

    if embed.description is None:
        embed.description = ""
    embed.description += "\n\n"
    
    rows_num: int = int(sqrt(len(view.children)))
    label: str = ""
    for i in range(rows_num):
        for j in range(rows_num):
            btn = view.children[(i * rows_num) + j]
            if not isinstance(btn, discord.ui.Button):
                embed.description += " ` ⚫ `"
                continue
            
            if btn.label is not None:
                label = btn.label
            
            if label == "\u1CBC":
                embed.description += " ` ⚫ `"
            elif label == "🟣":
                embed.description += " ` 🟣 `"
            else:
                embed.description += " ` 🟠 `"
            
            if j == rows_num - 1:
                embed.description += "\n"
    try:
        interaction: discord.Interaction = game_info["interaction"]
        await interaction.edit_original_response(embed=embed, view=None)
    except Exception as e:
        print(f"ERROR: Could not edit original message. \n{e}")
        pass