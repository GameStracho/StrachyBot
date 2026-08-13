import discord

import console
from shared import models, ui
from shared.types import Position, User

from .game import TicTacToeGame


class TicTacToeView(discord.ui.View):
    _game: TicTacToeGame
    message: discord.Message | None

    def __init__(self, game: TicTacToeGame, timeout: float = 15.0):
        super().__init__(timeout=timeout)

        self._game = game

        for x in range(game.get_grid_size()):
            for y in range(game.get_grid_size()):
                self.add_item(TicTacToeButton(parent_view=self, position=Position(x, y)))

        console.log_debug(
            f"/tic-tac-toe: New TicTacToeView created for game {self._game.get_match_id()} "
            f"with {timeout}s timeout."
        )

    def get_game(self) -> TicTacToeGame:
        return self._game

    def build_embed(self) -> tuple[discord.Embed, discord.File]:
        player_emoji, opponent_emoji = ui.get_player_emojis()
        player_color, _ = ui.get_player_colors()
        embed = discord.Embed(
            color=player_color,
            title="Tic-Tac-Toe",
            description=f"Connect {self._game.get_target_length()} cells to win.",
        )

        user: User = self._game.get_player()
        embed.set_author(name=user.display_name, icon_url=user.display_avatar)

        embed.add_field(
            name="Players",
            value=(
                f"{player_emoji} {self._game.get_player().mention}"
                f"\n{opponent_emoji} {self._game.get_opponent().mention}"
            ),
            inline=False,
        )
        embed.add_field(
            name="Status",
            value=f"It's {player_emoji} {self._game.get_player().mention}'s turn.",
            inline=False,
        )
        embed.add_field(name="Timeout", value=ui.get_timeout_timestamp(view=self), inline=False)

        icon, icon_url = ui.load_attachment(path=__file__, filename="icon.png")
        embed.set_thumbnail(url=icon_url)

        return (embed, icon)

    def update_embed(self, embed: discord.Embed) -> None:
        status_message: str = ""
        player_color, opponent_color = ui.get_player_colors()
        player: User = self._game.get_player()
        opponent: User = self._game.get_opponent()

        match self._game.get_status():
            case models.EMatchStatus.WIN | models.EMatchStatus.LOSS:
                winner: User | None = self._game.get_winner()
                assert winner

                embed.color = player_color if winner == player else opponent_color
                embed.set_author(name=winner.display_name, icon_url=winner.display_avatar)
                status_message = (
                    f"Player {winner.emoji} {winner.mention} won. " + ui.EMOJIS["game_win"]
                )
            case models.EMatchStatus.DRAW:
                embed.color = ui.COLORS["game_draw"]
                embed.set_author(name="", icon_url="")
                status_message = "Game ended in draw. " + ui.EMOJIS["game_draw"]
            case models.EMatchStatus.PENDING:
                current_player: User = player if self._game.is_players_turn() else opponent

                embed.color = player_color if self._game.is_players_turn() else opponent_color
                embed.set_author(
                    name=current_player.display_name,
                    icon_url=current_player.display_avatar,
                )
                status_message = (
                    f"It's {current_player.emoji} {current_player.mention}'s turn. "
                    + ui.EMOJIS["game_turn"]
                )
            case _:
                raise ValueError(self._game.get_status())

        if self._game.get_status() == models.EMatchStatus.PENDING:
            ui.embed.update_field(
                embed=embed,
                name="Timeout",
                value=ui.get_timeout_timestamp(view=self),
            )
        else:
            ui.embed.remove_field(embed=embed, name="Timeout")
            self.disable_buttons()
            self.stop()

        assert status_message
        ui.embed.update_field(embed=embed, name="Status", value=status_message)

    def disable_buttons(self) -> None:
        for child in self.children:
            if isinstance(child, TicTacToeButton):
                child.disabled = True

        console.log_debug(f"/tic-tac-toe: Buttons disabled for game {self._game.get_match_id()}.")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        try:
            current_player: User = (
                self._game.get_player()
                if self._game.is_players_turn()
                else self._game.get_opponent()
            )

            if interaction.user.id != current_player.id:
                console.log_debug(
                    f"Ineligible user {interaction.user.display_name} ({interaction.user.id}) "
                    f"tried to respond to game {self._game.get_match_id()}."
                )

                await interaction.response.send_message("It's not your turn!", ephemeral=True)
                return False  # Aborts processing and DOES NOT reset/extend the view timeout

            return True  # Authorized click; allow execution
        except Exception:
            await ui.handle_error(
                command="/tic-tac-toe", interaction=interaction, use_followup=False
            )
            return False

    async def on_timeout(self) -> None:
        if self._game.get_status() != models.EMatchStatus.PENDING or self.message is None:
            return

        self.disable_buttons()
        await self._game.handle_timeout()

        embed: discord.Embed = self.message.embeds[0]
        embed.color = ui.COLORS["game_timeout"]

        ui.embed.update_field(
            embed=embed, name="Status", value="Game timed out! " + ui.EMOJIS["game_timeout"]
        )
        ui.embed.remove_field(embed=embed, name="Timeout")

        # hide a second icon appearing above the embed
        embed.set_thumbnail(url="attachment://icon.png")

        # Edit the original message to show disabled buttons
        await self.message.edit(embed=embed, view=self)


class TicTacToeButton(discord.ui.Button[TicTacToeView]):
    _parent_view: TicTacToeView
    _position: Position

    def __init__(self, parent_view: TicTacToeView, position: Position) -> None:
        super().__init__(
            label=ui.EMOJIS["tic_empty_cell"], style=discord.ButtonStyle.secondary, row=position.y
        )

        self._parent_view = parent_view
        self._position = position

        console.log_debug(
            f"/tic-tac-toe: New TicTacToeButton created "
            f"for game {parent_view.get_game().get_match_id()}: pos = {position}."
        )

    def get_position(self) -> Position:
        return self._position

    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            game: TicTacToeGame = self._parent_view.get_game()

            success: bool = await game.play(position=self._position)

            if not success:
                await interaction.response.send_message("Invalid move! ☹️", ephemeral=True)
                return

            player_emoji, opponent_emoji = ui.get_player_emojis()
            self.label = opponent_emoji if game.is_players_turn() else player_emoji
            self.disabled = True

            # Check if opponent is a bot and should make an automatic counter-move
            if (
                game.get_status() == models.EMatchStatus.PENDING
                and game.get_opponent().is_bot
                and not game.is_players_turn()
            ):
                bot_pos: Position | None = game.calculate_bot_move()

                if bot_pos is not None:
                    await game.play(position=bot_pos)

                    # Disable button played by bot
                    for child in self._parent_view.children:
                        if isinstance(child, TicTacToeButton) and child.get_position() == bot_pos:
                            child.label = opponent_emoji
                            child.disabled = True
                            break

            embed: discord.Embed = ui.embed.extract(
                interaction=interaction, index=0, hide_icon=True
            )
            self._parent_view.update_embed(embed=embed)

            # Edit the original message to show disabled buttons
            await interaction.response.edit_message(embed=embed, view=self._parent_view)
        except Exception:
            await ui.handle_error(
                command="/tic-tac-toe", interaction=interaction, use_followup=False
            )
