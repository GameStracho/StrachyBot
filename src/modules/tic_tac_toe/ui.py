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
                self.add_item(TicTacToeButton(game_id=self._game.match_id, position=Position(x, y)))

        console.log_debug((
            f"/tic-tac-toe: New TicTacToeView created for game {self._game.match_id} "
            f"with {timeout}s timeout."
        ))


    def get_game(self) -> TicTacToeGame:
        return self._game


    def get_timeout_timestamp(self) -> str:
        return ui.get_timeout_timestamp(self._timeout) + "⏱️"
    
    
    def disable_buttons(self) -> None:
        for child in self.children:
            if isinstance(child, TicTacToeButton):
                child.disabled = True

        console.log_debug(f"/tic-tac-toe: Buttons disabled for game {self._game.match_id}.")


    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        try:
            current_player = self._game.get_player() if self._game.is_players_turn() else self._game.get_opponent()

            if interaction.user.id != current_player.id:
                console.log_debug(f"Ineligible user {interaction.user.display_name} ({interaction.user.id}) tried to respond to game {self._game.match_id}.")

                await interaction.response.send_message(
                    "It's not your turn!", 
                    ephemeral=True
                )
                return False  # Aborts processing and DOES NOT reset/extend the view timeout

            return True  # Authorized click; allow execution
        except Exception:
            await messages.handle_error(command="/tic-tac-toe", interaction=interaction, use_followup=False)


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
    _position: Position

    def __init__(self, game_id: int, position: Position) -> None:
        super().__init__(label="⬛", style=discord.ButtonStyle.secondary, row=position.y)

        self._position = position

        console.log_debug((
            f"/tic-tac-toe: New TicTacToeButton created for game {game_id}: "
            f"pos = {position}."
        ))

    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            parent_view = self.view
            assert isinstance(parent_view, TicTacToeView)

            game: TicTacToeGame = parent_view.get_game()

            player_emoji, opponent_emoji = get_player_emojis()
            self.label = player_emoji if game.is_players_turn() else opponent_emoji
            self.disabled = True

            success: bool = game.play(position=self._position)

            if not success:
                interaction.response.send_message("Invalid move! ☹️", ephemeral=True)
                return

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
                if game.is_players_turn():
                    embed.color = PLAYER_COLOR
                    ui.update_embed_field(embed=embed, name="Status", value=f"It's {player_emoji} {game.get_player().mention}'s turn. ⏳")
                else:
                    embed.color = OPPONENT_COLOR
                    ui.update_embed_field(embed=embed, name="Status", value=f"It's {opponent_emoji} {game.get_opponent().mention}'s turn. ⏳")

                ui.update_embed_field(embed=embed, name="Timeout", value=parent_view.get_timeout_timestamp())

            # Edit the original message to show disabled buttons
            await interaction.response.edit_message(embed=embed, view=parent_view)
        except Exception:
            await messages.handle_error(command="/tic-tac-toe", interaction=interaction, use_followup=False)
