from typing import override

import discord

from shared import logger, models, ui
from shared.types import Position, User

from .game import TicTacToeGame


class TicTacToeView(discord.ui.View):
    _game: TicTacToeGame
    message: discord.Message | None

    def __init__(self, game: TicTacToeGame, timeout: float = 15.0):
        super().__init__(timeout=timeout)

        self._game = game

        for x in range(game.grid_size):
            for y in range(game.grid_size):
                self.add_item(TicTacToeButton(parent_view=self, position=Position(x, y)))

        logger.debug(
            f"/tic-tac-toe: New TicTacToeView created for game {self._game.match_id} "
            f"with {timeout}s timeout."
        )

    @property
    def game(self) -> TicTacToeGame:
        return self._game

    def build_embed(self) -> tuple[discord.Embed, discord.File]:
        player_emoji, opponent_emoji = ui.get_player_emojis()
        player_color, _ = ui.get_player_colors()
        embed = discord.Embed(
            color=player_color,
            title="Tic-Tac-Toe",
            description=f"Connect {self._game.target_length} cells to win.",
        )

        user: User = self._game.player
        embed.set_author(name=user.display_name, icon_url=user.display_avatar)

        embed.add_field(
            name="Players",
            value=(
                f"{player_emoji} {self._game.player.mention}"
                f"\n{opponent_emoji} {self._game.opponent.mention}"
            ),
            inline=False,
        )
        embed.add_field(
            name="Status",
            value=f"It's {player_emoji} {self._game.player.mention}'s turn.",
            inline=False,
        )
        embed.add_field(name="Timeout", value=ui.get_timeout_timestamp(view=self), inline=False)

        icon, icon_url = ui.load_attachment(path=__file__, filename="icon.png")
        embed.set_thumbnail(url=icon_url)

        return (embed, icon)

    def update_embed(self, embed: discord.Embed) -> None:
        status_message: str = ""
        player_color, opponent_color = ui.get_player_colors()
        player: User = self._game.player
        opponent: User = self._game.opponent

        match self._game.status:
            case models.EMatchStatus.WIN | models.EMatchStatus.LOSS:
                winner: User | None = self._game.winner
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
                current_player: User = player if self._game.is_players_turn else opponent

                embed.color = player_color if self._game.is_players_turn else opponent_color
                embed.set_author(
                    name=current_player.display_name,
                    icon_url=current_player.display_avatar,
                )
                status_message = (
                    f"It's {current_player.emoji} {current_player.mention}'s turn. "
                    + ui.EMOJIS["game_turn"]
                )
            case _:
                raise ValueError(self._game.status)

        if self._game.status == models.EMatchStatus.PENDING:
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

        logger.debug(f"/tic-tac-toe: Buttons disabled for game {self._game.match_id}.")

    @override
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        try:
            current_player: User = (
                self._game.player if self._game.is_players_turn else self._game.opponent
            )

            if interaction.user.id != current_player.id:
                logger.debug(
                    f"Ineligible user {interaction.user.display_name} ({interaction.user.id}) "
                    f"tried to respond to game {self._game.match_id}."
                )

                embed, icon = ui.embed.build_warning(message="It's not your turn!")

                await interaction.response.send_message(embed=embed, file=icon, ephemeral=True)
                return False  # Aborts processing and DOES NOT reset/extend the view timeout

            return True  # Authorized click; allow execution
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)
            return False

    @override
    async def on_timeout(self) -> None:
        if self._game.status != models.EMatchStatus.PENDING or self.message is None:
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

        logger.debug(
            f"/tic-tac-toe: New TicTacToeButton created "
            f"for game {parent_view.game.match_id}: pos = {position}."
        )

    @property
    def position(self) -> Position:
        return self._position

    @override
    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            game: TicTacToeGame = self._parent_view.game

            success: bool = await game.play(position=self._position)

            if not success:
                warning_embed, warning_icon = ui.embed.build_warning(message="Invalid move! ☹️")

                await interaction.response.send_message(
                    embed=warning_embed, file=warning_icon, ephemeral=True
                )
                return

            player_emoji, opponent_emoji = ui.get_player_emojis()
            self.label = opponent_emoji if game.is_players_turn else player_emoji
            self.disabled = True

            # Check if opponent is a bot and should make an automatic counter-move
            if (
                game.status == models.EMatchStatus.PENDING
                and game.opponent.is_bot
                and not game.is_players_turn
            ):
                bot_pos: Position | None = game.calculate_bot_move()

                if bot_pos is not None:
                    await game.play(position=bot_pos)

                    # Disable button played by bot
                    for child in self._parent_view.children:
                        if isinstance(child, TicTacToeButton) and child.position == bot_pos:
                            child.label = opponent_emoji
                            child.disabled = True
                            break

            embed: discord.Embed = ui.embed.extract(target=interaction, index=0, hide_icon=True)
            self._parent_view.update_embed(embed=embed)

            # Edit the original message to show disabled buttons
            await interaction.response.edit_message(embed=embed, view=self._parent_view)
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)
