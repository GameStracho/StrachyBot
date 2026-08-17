from datetime import UTC, datetime
from typing import override

import discord

from shared import logger, models, types, ui

from .game import WordleGame, WordleLetterCategory


class WordleView(discord.ui.View):
    _game: WordleGame
    _spoiler: str
    message: discord.Message | None

    def __init__(self, game: WordleGame, timeout: float = 180):
        super().__init__(timeout=timeout)

        self._game = game
        logger.debug(
            f"/trivia: New WordleView created for game {self._game.match_id}"
            f" with {timeout}s timeout."
        )

    @property
    def game(self) -> WordleGame:
        return self._game

    def build_embed(self) -> tuple[discord.Embed, discord.File]:
        title: str = "Wordle"
        user: types.User = self._game.player

        if self._game.is_daily:
            title += f" {datetime.now(tz=UTC).date().strftime('%Y-%m-%d')}"

        embed: discord.Embed = discord.Embed(title=title, color=discord.Color.blue())
        embed.set_author(name=user.display_name, icon_url=user.display_avatar)

        empty_word: str = ui.EMOJIS["wordle_unused_letter"]

        for i in range(4):
            empty_word += " " + ui.EMOJIS["wordle_unused_letter"]

        for i in range(6):
            embed.add_field(name="Guess #" + str(i + 1), value=empty_word, inline=False)

        embed.add_field(name="Used letters", value=self._color_available_letters(), inline=False)
        embed.add_field(name="Status", value="Game started. You can start guessing.", inline=True)
        embed.add_field(name="Timeout", value=ui.get_timeout_timestamp(self), inline=True)

        icon, icon_url = ui.load_attachment(path=__file__, filename="icon.png")
        embed.set_thumbnail(url=icon_url)

        return (embed, icon)

    def update_embed(self, embed: discord.Embed, default_status: str) -> None:
        last_guess: str = self._game.last_guess
        ui.embed.update_field(
            embed=embed,
            name=f"Guess #{self._game.guesses_count}",
            value=self._uncover_word(word=last_guess),
        )
        ui.embed.update_field(
            embed=embed, name="Used letters", value=self._color_available_letters()
        )

        match self._game.status:
            case models.EMatchStatus.PENDING:
                ui.embed.update_field(embed=embed, name="Status", value=default_status)
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
                        f"The secret word was '{self.spoil(self._game.secret_word)}'."
                    ),
                )
            case models.EMatchStatus.SURRENDER:
                embed.color = ui.COLORS["white"]
                ui.embed.update_field(
                    embed=embed,
                    name="Status",
                    value=(
                        f"You gave up! {ui.EMOJIS['game_surrender']}\n"
                        f"The secret word was '{self.spoil(self._game.secret_word)}'."
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
        logger.debug(f"/wordle: Buttons disabled for game {self._game.match_id}.")

    def spoil(self, string: str) -> str:
        spoiler = "||" if self._game.is_daily else ""
        return f"{spoiler}{string}{spoiler}"

    def _get_letter_category_emoji(self, category: WordleLetterCategory) -> str:
        match category:
            case WordleLetterCategory.CORRECT:
                return ui.EMOJIS["wordle_correct_letter"]
            case WordleLetterCategory.MISPLACED:
                return ui.EMOJIS["wordle_misplaced_letter"]
            case WordleLetterCategory.INCORRECT:
                return ui.EMOJIS["wordle_incorrect_letter"]
            case WordleLetterCategory.UNUSED:
                return ui.EMOJIS["wordle_unused_letter"]
            case _:
                raise ValueError(category)

    def _uncover_word(self, word: str) -> str:
        """
        Turns every letter of a given word into emojis and adds color coded line under the word
        signalling whether the guessed letter is in a correct spot, misplaced or completely missing
        based on the game's secret word.

        Returns the color coded word.
        """
        categorized_word: list[tuple[str, WordleLetterCategory]] = self._game.categorize_word(
            word=word
        )
        uncovered_letters: str = ""
        uncovered_colors: str = ""

        for letter, category in categorized_word:
            uncovered_letters += ui.EMOJIS[letter] + " "
            uncovered_colors += self._get_letter_category_emoji(category=category) + " "

        return f"{self.spoil(uncovered_letters.rstrip())}\n{uncovered_colors.rstrip()}"

    def _color_available_letters(self) -> str:
        """
        Turns every letter from available letters into emojis and adds color coded line under them
        signalling their category.

        Returns the color coded available letters.
        """
        available_letters: dict[str, WordleLetterCategory] = self._game.available_letters
        uncovered_letters: str = ""
        uncovered_colors: str = ""
        result: str = ""

        for letter, category in available_letters.items():
            uncovered_letters += ui.EMOJIS[letter] + " "
            uncovered_colors += self._get_letter_category_emoji(category=category) + " "

            if len(uncovered_letters) == len(available_letters):
                result += f"\n\n{uncovered_letters.rstrip()}\n{self.spoil(uncovered_colors)}"
                uncovered_letters = ""
                uncovered_colors = ""

        return result

    @override
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        try:
            if interaction.user.id != self._game.player.id:
                logger.warning(
                    f"/wordle: Ineligible user {interaction.user.display_name} "
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
        self.disable_buttons()

        embed: discord.Embed = ui.embed.extract(target=self.message, index=0, hide_icon=True)
        ui.embed.remove_field(embed=embed, name="Timeout")
        ui.embed.update_field(
            embed=embed,
            name="Status",
            value=(
                f"Game timed out! {ui.EMOJIS['game_timeout']} "
                f"The secret word was '{self.spoil(self._game.secret_word)}'."
            ),
        )

        # Edit the original message to show disabled buttons
        await self.message.edit(embed=embed, view=self)

    @discord.ui.button(
        label="Enter guess",
        style=discord.ButtonStyle.primary,
        emoji=ui.EMOJIS["wordle_enter_guess_button"],
    )
    async def enter_guess_button(
        self, interaction: discord.Interaction, button: discord.ui.Button["WordleView"]
    ) -> None:
        try:
            logger.debug(
                f"/wordle: User {interaction.user.display_name} ({interaction.user.id}) "
                f"pressed the 'Enter guess' button for game {self._game.match_id}."
            )

            assert self.message is not None
            embed: discord.Embed = ui.embed.extract(target=self.message, index=0, hide_icon=True)
            ui.embed.update_field(embed=embed, name="Timeout", value=ui.get_timeout_timestamp(self))
            await self.message.edit(embed=embed, view=self)

            modal: WordleGuessModal = WordleGuessModal(parent_view=self)
            await interaction.response.send_modal(modal)

            logger.debug(
                f"/wordle: Modal for game {self._game.match_id} "
                f"sent to User {interaction.user.display_name} ({interaction.user.id})."
            )
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)

    @discord.ui.button(
        label="Random guess",
        style=discord.ButtonStyle.secondary,
        emoji=ui.EMOJIS["wordle_random_guess_button"],
    )
    async def random_guess_button(
        self, interaction: discord.Interaction, button: discord.ui.Button["WordleView"]
    ) -> None:
        try:

            async def handle_random_guess(confirm_interaction: discord.Interaction) -> None:
                logger.debug(
                    f"/wordle: User {confirm_interaction.user.display_name} "
                    f"({confirm_interaction.user.id}) "
                    f"pressed the 'Random guess' button for game {self._game.match_id}."
                )

                assert self.message is not None
                embed: discord.Embed = ui.embed.extract(
                    target=self.message, index=0, hide_icon=True
                )

                await self._game.guess_random_word()
                self.update_embed(embed=embed, default_status="Used random guess.")
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
                on_confirm=handle_random_guess,
                confirm_label="Yes",
                cancel_label="No",
                timeout=timeout,
            )
            confirm_embed, confirm_icon = confirm_view.build_embed(
                question="Are you sure you want to use a random guess?"
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
        self, interaction: discord.Interaction, button: discord.ui.Button["WordleView"]
    ) -> None:
        try:

            async def handle_surrender(confirm_interaction: discord.Interaction) -> None:
                logger.debug(
                    f"/wordle: User {confirm_interaction.user.display_name} "
                    f"({confirm_interaction.user.id}) "
                    f"pressed the 'Give up' button for game {self._game.match_id}."
                )

                assert self.message is not None
                embed: discord.Embed = ui.embed.extract(
                    target=self.message, index=0, hide_icon=True
                )

                await self._game.handle_surrender()
                self.update_embed(embed=embed, default_status="Used random guess.")
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


class WordleGuessModal(discord.ui.Modal):
    _parent_view: WordleView

    def __init__(self, parent_view: WordleView):
        super().__init__(title="Wordle Guess")

        self._parent_view = parent_view
        logger.debug(
            f"/wordle: New WordleGuessModal created for game {self._parent_view.game.match_id}."
        )

    guess_input: discord.ui.TextInput["WordleGuessModal"] = discord.ui.TextInput(
        label="Guess",
        style=discord.TextStyle.short,
        placeholder="Enter a 5-letter word",
        min_length=5,
        max_length=5,
        required=True,
    )

    def _get_uncovered_guess(self) -> str:
        secret_word: str = self._parent_view.game.secret_word
        guess: str = self.guess_input.value.lower()
        uncovered_letters: str = ""
        uncovered_colors: str = ""

        for i, letter in enumerate(guess):
            uncovered_letters += ui.EMOJIS[letter] + " "
            sw_count: int = secret_word.count(letter)

            if letter == secret_word[i]:
                uncovered_colors += ui.EMOJIS["wordle_correct_letter"] + " "
            elif (
                letter in secret_word
                and guess[:i].count(letter) < sw_count
                and guess[i:].count(letter) <= sw_count
            ):
                uncovered_colors += ui.EMOJIS["wordle_misplaced_letter"] + " "
            else:
                uncovered_colors += ui.EMOJIS["wordle_incorrect_letter"] + " "

        return uncovered_letters.rstrip() + "\n" + uncovered_colors.rstrip()

    @override
    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            game: WordleGame = self._parent_view.game
            guess: str = self.guess_input.value.lower()
            updated_status: str = ""

            embed: discord.Embed = ui.embed.extract(target=interaction, index=0, hide_icon=True)

            if not game.is_valid_word(guess):
                logger.info(
                    f"/wordle: User {interaction.user.display_name} ({interaction.user.id}) "
                    f"entered an invalid word '{guess}'."
                )
                updated_status = f"Entered invalid word '{self._parent_view.spoil(guess)}'."
            elif game.is_previous_guess(word=guess):
                logger.info(
                    f"/wordle: User {interaction.user.display_name} ({interaction.user.id}) "
                    f"entered an already guesses word '{guess}'."
                )
                updated_status = f"You already guessed the word '{self._parent_view.spoil(guess)}'."
            else:
                await game.add_guess(word=guess)
                logger.info(
                    f"/wordle: User {interaction.user.display_name} ({interaction.user.id}) "
                    f"guessed '{self.guess_input.value}' "
                    f"in game {self._parent_view.game.match_id}."
                )
                updated_status = "Valid guess."

            self._parent_view.update_embed(embed=embed, default_status=updated_status)
            await interaction.response.edit_message(embed=embed, view=self._parent_view)
            self._parent_view.message = await interaction.original_response()
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)
