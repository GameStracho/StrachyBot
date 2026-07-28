from typing import Tuple
import discord
from datetime import datetime, timezone

from shared import console, messages, ui
from shared.types import Position
from .game import TicTacToeGame

PLAYER_COLOR: discord.Color = discord.Color.purple()
OPPONENT_COLOR: discord.Color = discord.Color.orange()


def get_player_emojis(date: datetime = datetime.now(timezone.utc)) -> Tuple[str, str]:
    """
    Returns player's and opponent's emojis based on selected date.
    """

    # Valentine's day
    if date.day == 14 and date.month == 2:
        return ("💜", "🧡")

    return ("🟣", "🟠")


class TicTacToeView(discord.ui.View):
    _timeout: float
    _game: TicTacToeGame
    message: discord.Message | None

    def __init__(self, game: TicTacToeGame, timeout: float = 15.0):
        super().__init__(timeout=timeout)

        self._game = game
        self._timeout = timeout

        for x in range(game.get_grid_size()):
            for y in range(game.get_grid_size()):
                self.add_item(TicTacToeButton(game_id=self._game.match_id, pos=Position(x, y)))

        console.log_debug((
            f"/tic-tac-toe: New TicTacToeView created for game {self._game.match_id} "
            f"with {timeout}s timeout."
        ))


    def get_game(self) -> TicTacToeGame:
        return self._game


    def reset_timeout(self) -> None:
        self.timeout = self._timeout


    def get_timeout_timestamp(self) -> str:
        return ui.get_timeout_timestamp(self._timeout) + "⏱️"
    
    
    def disable_buttons(self) -> None:
        for child in self.children:
            if isinstance(child, TicTacToeButton):
                child.disabled = True

        console.log_debug(f"/tic-tac-toe: Buttons disabled for game {self._game.match_id}.")


    async def on_timeout(self) -> None:
        if self._game.has_game_ended() or self.message is None:
            return

        console.log_info(f"/tic-tac-toe: Game {self._game.match_id} timed out.")
        self.disable_buttons()

        embed: discord.Embed = self.message.embeds[0]
        embed.color = ui.TIMEOUT_COLOR

        ui.update_embed_field(embed=embed, name="Status", value="Game timed out! ⏰")
        ui.remove_embed_field(embed=embed, name="Timeout")

        # hide a second icon appearing above the embed
        embed.set_thumbnail(url="attachment://icon.png")

        # Edit the original message to show disabled buttons
        await self.message.edit(embed=embed, view=self)


class TicTacToeButton(discord.ui.Button["TicTacToeView"]):
    pos: Position

    def __init__(self, game_id: int, pos: Position) -> None:
        super().__init__(label="⬛", style=discord.ButtonStyle.secondary, row=pos.y)

        console.log_debug((
            f"/tic-tac-toe: New TicTacToeButton created for game {game_id}: "
            f"pos = {pos}."
        ))

    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            player_emoji, opponent_emoji = get_player_emojis()

            parent_view = self.view
            assert isinstance(parent_view, TicTacToeView)

            game: TicTacToeGame = parent_view.get_game()

            self.label = player_emoji if game.is_players_turn() else opponent_emoji
            self.disabled = True

            game.play(pos=self.pos)

            message: discord.Message | None = interaction.message
            assert message is not None

            embed: discord.Embed = message.embeds[0]

            # hide a second icon appearing above the embed
            embed.set_thumbnail(url="attachment://icon.png")

            if game.has_game_ended():
                winner: discord.User | None = game.get_winner()

                if not winner:
                    embed.color = ui.DRAW_COLOR
                    ui.update_embed_field(embed=embed, name="Status", value="Game ended in draw. 🤝")
                elif winner == game.get_player():
                    embed.color = PLAYER_COLOR
                    ui.update_embed_field(embed=embed, name="Status", value=f"Player {player_emoji} {game.get_player().mention} won. 🎉")
                else:
                    embed.color = OPPONENT_COLOR
                    ui.update_embed_field(embed=embed, name="Status", value=f"Player {opponent_emoji} {game.get_opponent().mention} won. 🎉")
            else:
                parent_view.reset_timeout()
                ui.update_embed_field(embed=embed, name="Timeout", value=parent_view.get_timeout_timestamp())

                if game.is_players_turn():
                    embed.color = PLAYER_COLOR
                    ui.update_embed_field(embed=embed, name="Status", value=f"It's {player_emoji} {game.get_player().mention}'s turn. ⏳")
                else:
                    embed.color = OPPONENT_COLOR
                    ui.update_embed_field(embed=embed, name="Status", value=f"It's {opponent_emoji} {game.get_opponent().mention}'s turn. ⏳")

            # Edit the original message to show disabled buttons
            await interaction.response.edit_message(embed=embed, view=parent_view)
        except Exception:
            await messages.handle_error(command="/tic-tac-toe", interaction=interaction, use_followup=False)
