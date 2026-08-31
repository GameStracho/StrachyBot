from datetime import UTC, datetime

import discord
from typing_extensions import override

from shared import logger, models, types, ui

from .game import EGuessCategory, Game
from .models import SonglessSong

active_game_views: dict[int, "View"] = {}


class View(discord.ui.View):
    _game: Game
    message: discord.Message | None

    def __init__(self, game: Game, timeout: float = 180):
        super().__init__(timeout=timeout)

        self._game = game
        logger.debug(
            f"New SonglessView created for game {self._game.match_id} with {timeout}s timeout."
        )

        if active_game_views.get(game.match_id):
            raise RuntimeError(f"Active game with id '{game.match_id}' already exists.")
        active_game_views[game.match_id] = self

    @property
    def game(self) -> Game:
        return self._game

    def build_embed(self) -> tuple[discord.Embed, list[discord.File]]:
        title: str = "Songless"
        user: types.User = self._game.player

        if self._game.is_daily:
            title += f" {datetime.now(tz=UTC).date().strftime('%Y-%m-%d')}"

        embed: discord.Embed = discord.Embed(
            title=title + f" - {self._game.category}", color=discord.Color.gold()
        )
        embed.set_author(name=user.display_name, icon_url=user.display_avatar)

        for i in range(6):
            embed.add_field(
                name="Turn #" + str(i + 1), value=ui.EMOJIS["songless_empty_guess"], inline=False
            )

        embed.add_field(name="Status", value="Game started. You can start guessing.", inline=True)
        embed.add_field(name="Timeout", value=ui.get_timeout_timestamp(self), inline=True)

        icon, icon_url = ui.load_attachment(path=__file__, filename="icon.png")
        embed.set_thumbnail(url=icon_url)

        snippet: discord.File = discord.File(fp=self._game.snippet, filename="snippet.mp3")

        return (embed, [icon, snippet])

    def update_embed(
        self,
        embed: discord.Embed,
        default_status: str,
        last_guess: tuple[SonglessSong | None, EGuessCategory] | None = None,
    ) -> None:
        if last_guess:
            ui.embed.update_field(
                embed=embed,
                name=f"Turn #{len(self._game.guesses)}",
                value=self._uncover_guess(song=last_guess[0], category=last_guess[1]),
            )

        match self._game.status:
            case models.EMatchStatus.PENDING:
                ui.embed.update_field(embed=embed, name="Status", value=self.spoil(default_status))
                ui.embed.update_field(
                    embed=embed, name="Timeout", value=ui.get_timeout_timestamp(self)
                )
                return
            case models.EMatchStatus.WIN:
                embed.color = discord.Color.green()
                ui.embed.update_field(
                    embed=embed, name="Status", value="You won! " + ui.EMOJIS["game_win"]
                )
            case models.EMatchStatus.LOSS:
                embed.color = discord.Color.red()
                ui.embed.update_field(
                    embed=embed,
                    name="Status",
                    value=(
                        f"You lost! {ui.EMOJIS['game_loss']}\n"
                        f"The secret song was '{self.spoil(self._game.song_str)}'."
                    ),
                )
            case models.EMatchStatus.SURRENDER:
                embed.color = ui.COLORS["white"]
                ui.embed.update_field(
                    embed=embed,
                    name="Status",
                    value=(
                        f"You gave up! {ui.EMOJIS['game_surrender']}\n"
                        f"The secret word was '{self.spoil(self._game.song_str)}'."
                    ),
                )
            case models.EMatchStatus.TIMEOUT:
                ui.embed.update_field(
                    embed=embed,
                    name="Status",
                    value=(
                        f"Game timed out! {ui.EMOJIS['game_timeout']} "
                        f"The secret song was '{self.spoil(self._game.song_str)}'."
                    ),
                )
            case _:
                raise ValueError(self._game.status)

        self.disable_buttons()
        ui.embed.remove_field(embed=embed, name="Timeout")
        self.stop()

    def disable_buttons(self) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        logger.debug(f"Buttons disabled for game {self._game.match_id}.")

        active_game_views.pop(self._game.match_id)

    def spoil(self, string: str) -> str:
        spoiler = "||" if self._game.is_daily else ""
        return f"{spoiler}{string}{spoiler}"

    def _get_guess_category_emoji(self, category: EGuessCategory) -> str:
        match category:
            case EGuessCategory.EMPTY:
                return ui.EMOJIS["songless_empty_guess"]
            case EGuessCategory.INCORRECT:
                return ui.EMOJIS["songless_incorrect_guess"]
            case EGuessCategory.ARTIST:
                return ui.EMOJIS["songless_artist_guess"]
            case EGuessCategory.CORRECT:
                return ui.EMOJIS["songless_correct_guess"]
            case _:
                raise ValueError(category)

    def _uncover_guess(self, song: SonglessSong | None, category: EGuessCategory) -> str:
        """
        Adds an emoji in front of the song title and author based on
        the category of the guess.

        Returns the color coded word.
        """
        song_str = f"{song.title} - {song.artist}" if song else "Skipped"
        emoji: str = ""

        match category:
            case EGuessCategory.EMPTY:
                emoji = ui.EMOJIS["songless_empty_guess"]
            case EGuessCategory.INCORRECT:
                emoji = ui.EMOJIS["songless_incorrect_guess"]
            case EGuessCategory.ARTIST:
                emoji = ui.EMOJIS["songless_artist_guess"]
            case EGuessCategory.CORRECT:
                emoji = ui.EMOJIS["songless_correct_guess"]
            case _:
                raise ValueError(category)

        return f"{emoji} {self.spoil(song_str)}"

    @override
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        try:
            if interaction.user.id != self._game.player.id:
                logger.warning(
                    f"Ineligible user {interaction.user.display_name} "
                    f"({interaction.user.id}) "
                    f"responded to game {self._game.match_id}."
                )

                embed, icon = ui.embed.build_warning(message="You cannot respond to this game.")

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

        await self._game.handle_timeout()

        embed: discord.Embed = ui.embed.extract(target=self.message, index=0, hide_icon=True)
        self.update_embed(embed=embed, default_status="Timeout")

        # Edit the original message to show disabled buttons
        await self.message.edit(embed=embed, view=self)

    @discord.ui.button(
        label="Skip",
        style=discord.ButtonStyle.secondary,
        emoji=ui.EMOJIS["songless_skip_button"],
    )
    async def skip_button(
        self, interaction: discord.Interaction, button: discord.ui.Button["View"]
    ) -> None:
        try:

            async def handle_random_guess(confirm_interaction: discord.Interaction) -> None:
                logger.debug(
                    f"User {confirm_interaction.user.display_name} "
                    f"({confirm_interaction.user.id}) "
                    f"pressed the 'Skip' button for game {self._game.match_id}."
                )

                assert self.message is not None
                embed: discord.Embed = ui.embed.extract(
                    target=self.message, index=0, hide_icon=True
                )

                await self._game.handle_skip()
                self.update_embed(
                    embed=embed,
                    default_status=f"Skipped turn #{len(self._game.guesses)}.",
                    last_guess=(None, EGuessCategory.INCORRECT),
                )

                files: list[discord.File] = []

                if self.game.status == models.EMatchStatus.PENDING:
                    files.append(discord.File(fp=self.game.snippet, filename="snippet.mp3"))

                await self.message.edit(embed=embed, view=self, attachments=files)

            assert self.message is not None
            songless_embed: discord.Embed = ui.embed.extract(
                target=self.message, index=0, hide_icon=True
            )
            ui.embed.update_field(
                embed=songless_embed, name="Timeout", value=ui.get_timeout_timestamp(self)
            )

            await self.message.edit(embed=songless_embed, view=self)

            timeout: float = min(self.timeout, 30.0) if self.timeout else 30.0
            confirm_view: ui.ConfirmView = ui.ConfirmView(
                interaction=interaction,
                on_confirm=handle_random_guess,
                confirm_label="Yes",
                cancel_label="No",
                timeout=timeout,
            )
            confirm_embed, confirm_icon = confirm_view.build_embed(
                question="Are you sure you want to skip this turn?"
            )

            await interaction.response.send_message(
                embed=confirm_embed, view=confirm_view, file=confirm_icon, ephemeral=True
            )
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)

    @discord.ui.button(
        label="Give up", style=discord.ButtonStyle.secondary, emoji=ui.EMOJIS["game_surrender"]
    )
    async def give_up_button(
        self, interaction: discord.Interaction, button: discord.ui.Button["View"]
    ) -> None:
        try:

            async def handle_surrender(confirm_interaction: discord.Interaction) -> None:
                logger.debug(
                    f"User {confirm_interaction.user.display_name} "
                    f"({confirm_interaction.user.id}) "
                    f"pressed the 'Give up' button for game {self._game.match_id}."
                )

                assert self.message is not None
                embed: discord.Embed = ui.embed.extract(
                    target=self.message, index=0, hide_icon=True
                )

                await self._game.handle_surrender()
                self.update_embed(embed=embed, default_status="You gave up!")
                await self.message.edit(embed=embed, view=self)

            assert self.message is not None
            wordle_embed: discord.Embed = ui.embed.extract(
                target=self.message, index=0, hide_icon=True
            )
            ui.embed.update_field(
                embed=wordle_embed, name="Timeout", value=ui.get_timeout_timestamp(self)
            )
            await self.message.edit(embed=wordle_embed, view=self)

            timeout: float = min(self.timeout, 30.0) if self.timeout else 30.0
            confirm_view: ui.ConfirmView = ui.ConfirmView(
                interaction=interaction,
                on_confirm=handle_surrender,
                confirm_label="Yes",
                cancel_label="No",
                timeout=timeout,
            )
            confirm_embed, confirm_icon = confirm_view.build_embed(
                question="Are you sure you want to give up?"
            )

            await interaction.response.send_message(
                embed=confirm_embed, view=confirm_view, file=confirm_icon, ephemeral=True
            )
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)
