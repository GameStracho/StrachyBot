
import discord

from shared import console, helpers, messages, models, ui
from shared.types import Position

from .game import TicTacToeGame
from .repository import update_match


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

        console.log_debug(
            f"/tic-tac-toe: New TicTacToeView created for game {self._game.match_id} "
            f"with {timeout}s timeout."
        )


    def get_game(self) -> TicTacToeGame:
        return self._game
    
    
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
            return False


    async def on_timeout(self) -> None:
        if self._game.has_game_ended() or self.message is None:
            return

        console.log_info(f"/tic-tac-toe: Game {self._game.match_id} timed out.")
        self.disable_buttons()

        embed: discord.Embed = self.message.embeds[0]
        embed.color = ui.TIMEOUT_COLOR

        ui.update_embed_field(embed=embed, name="Status", value="Game timed out! " + ui.EMOJIS["game_timeout"])
        ui.remove_embed_field(embed=embed, name="Timeout")

        # hide a second icon appearing above the embed
        embed.set_thumbnail(url="attachment://icon.png")

        await helpers.execute_db_operation(
            target=self.message, db_func=update_match,
            match_id=self._game.match_id, status=models.EMatchStatus.TIMEOUT, total_moves=self._game.get_total_moves()
        )

        # Edit the original message to show disabled buttons
        await self.message.edit(embed=embed, view=self)


class TicTacToeButton(discord.ui.Button[TicTacToeView]):
    _position: Position

    def __init__(self, game_id: int, position: Position) -> None:
        super().__init__(label=ui.EMOJIS["tic_empty_cell"], style=discord.ButtonStyle.secondary, row=position.y)

        self._position = position

        console.log_debug(
            f"/tic-tac-toe: New TicTacToeButton created for game {game_id}: "
            f"pos = {position}."
        )


    def get_position(self) -> Position:
        return self._position


    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            parent_view = self.view
            assert isinstance(parent_view, TicTacToeView)

            game: TicTacToeGame = parent_view.get_game()

            success: bool = game.play(position=self._position)

            if not success:
                await interaction.response.send_message("Invalid move! ☹️", ephemeral=True)
                return

            message: discord.Message | None = interaction.message
            assert message is not None

            embed: discord.Embed = message.embeds[0]

            player_emoji, opponent_emoji = ui.get_player_emojis()
            self.label = opponent_emoji if game.is_players_turn() else player_emoji
            self.disabled = True

            # hide a second icon appearing above the embed
            embed.set_thumbnail(url="attachment://icon.png")

            # Check if opponent is a bot and should make an automatic counter-move
            if not game.has_game_ended() and game.is_opponent_bot() and not game.is_players_turn():
                bot_pos: Position | None = game.calculate_bot_move()

                if bot_pos is not None:
                    game.play(position=bot_pos)

                    # Disable button played by bot
                    for child in parent_view.children:
                        if isinstance(child, TicTacToeButton) and child.get_position() == bot_pos:
                            child.label = opponent_emoji
                            child.disabled = True
                            break

            status_message: str = ""
            player_color, opponent_color = ui.get_player_colors()

            if game.has_game_ended():
                winner: discord.User | None = game.get_winner()
                status: models.EMatchStatus = models.EMatchStatus.PENDING

                ui.remove_embed_field(embed=embed, name="Timeout")
                parent_view.disable_buttons()

                if not winner:
                    embed.color = ui.DRAW_COLOR
                    status_message = "Game ended in draw. " + ui.EMOJIS["game_draw"]
                    status = models.EMatchStatus.DRAW
                elif winner == game.get_player():
                    embed.color = player_color
                    status_message = f"Player {player_emoji} {game.get_player().mention} won. " + ui.EMOJIS["game_win"]
                    status = models.EMatchStatus.WIN
                else:
                    embed.color = opponent_color
                    status_message = f"Player {opponent_emoji} {game.get_opponent().mention} won. " + ui.EMOJIS["game_win"]
                    status = models.EMatchStatus.LOSS

                await helpers.execute_db_operation(
                    target=interaction, db_func=update_match,
                    match_id=parent_view.get_game().match_id, status=status, total_moves=parent_view.get_game().get_total_moves()
                )
            else:
                if game.is_players_turn():
                    embed.color = player_color
                    status_message = f"It's {player_emoji} {game.get_player().mention}'s turn. " + ui.EMOJIS["game_turn"]
                else:
                    embed.color = opponent_color
                    status_message = f"It's {opponent_emoji} {game.get_opponent().mention}'s turn. " + ui.EMOJIS["game_turn"]

                ui.update_embed_field(embed=embed, name="Timeout", value=ui.get_timeout_timestamp(view=parent_view))

            assert status_message
            ui.update_embed_field(embed=embed, name="Status", value=status_message)

            # Edit the original message to show disabled buttons
            await interaction.response.edit_message(embed=embed, view=parent_view)
        except Exception:
            await messages.handle_error(command="/tic-tac-toe", interaction=interaction, use_followup=False)
