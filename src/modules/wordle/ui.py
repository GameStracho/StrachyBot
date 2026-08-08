import discord

from shared import console, helpers, messages, ui

from .game import WordleGame, WordleLetterCategory


class WordleView(discord.ui.View):
    _game: WordleGame
    message: discord.Message | None

    def __init__(self, game: WordleGame, timeout: float = 180):
        super().__init__(timeout=timeout)

        self._game = game
        console.log_debug(f"/trivia: New WordleView created for game {self._game.match_id} with {timeout}s timeout.")

    def get_game(self) -> WordleGame:
        return self._game

    def build_embed(self, user: discord.User | discord.Member) -> tuple[discord.Embed, discord.File]:
        embed: discord.Embed = discord.Embed(title="Wordle", color=discord.Color.blue())
        embed.set_author(name=user.display_name, icon_url=user.display_avatar)

        empty_word: str = ui.EMOJIS["wordle_unused_letter"]

        for i in range(4):
            empty_word += " " + ui.EMOJIS["wordle_unused_letter"]

        for i in range(6):
            embed.add_field(name="Guess #" + str(i + 1), value=empty_word, inline=False)

        embed.add_field(name="Used letters", value=self._color_available_letters(), inline=False)
        embed.add_field(name="Status", value="Game started. You can start guessing.", inline=True)
        embed.add_field(name="Timeout", value=ui.get_timeout_timestamp(self), inline=True)

        icon, icon_url = helpers.load_attachment(path=__file__, filename="icon.png")
        embed.set_thumbnail(url=icon_url)

        return (embed, icon)

    def disable_buttons(self) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        console.log_debug(f"/wordle: Buttons disabled for game {self._game.match_id}.")

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
        categorized_word: list[tuple[str, WordleLetterCategory]] = self._game.categorize_word(word=word)
        uncovered_letters: str = ""
        uncovered_colors: str = ""

        for letter, category in categorized_word:
            uncovered_letters += ui.EMOJIS[letter] + " "
            uncovered_colors += self._get_letter_category_emoji(category=category) + " "

        return uncovered_letters.rstrip() + "\n" + uncovered_colors.rstrip()

    def _color_available_letters(self) -> str:
        """
            Turns every letter from available letters into emojis and adds color coded line under them
            signalling their category.

            Returns the color coded available letters.
        """
        available_letters: dict[str, WordleLetterCategory] = self._game.get_available_letters()
        uncovered_letters: str = ""
        uncovered_colors: str = ""
        result: str = ""

        for letter, category in available_letters.items():
            uncovered_letters += ui.EMOJIS[letter] + " "
            uncovered_colors += self._get_letter_category_emoji(category=category) + " "

            if len(uncovered_letters) == len(available_letters):
                result += f"\n\n{uncovered_letters.rstrip()}\n{uncovered_colors}"
                uncovered_letters = "" 
                uncovered_colors = ""

        return result + f"\n\n{uncovered_letters.rstrip()}\n{uncovered_colors}"

    def update_embed(self, embed: discord.Embed, user: discord.User | discord.Member, default_status: str) -> None:
        last_guess: str = self._game.get_last_guess()
        ui.update_embed_field(embed=embed, name=f"Guess #{self._game.get_guesses_count()}", value=self._uncover_word(word=last_guess))
        ui.update_embed_field(embed=embed, name="Used letters", value=self._color_available_letters())
        
        if not self._game.is_over():
            ui.update_embed_field(embed=embed, name="Status", value=default_status)
            ui.update_embed_field(embed=embed, name="Timeout", value=ui.get_timeout_timestamp(self))
            return

        self.disable_buttons()
        ui.remove_embed_field(embed=embed, name="Timeout")
        self.stop()

        if last_guess == self._game.get_secret_word():
            console.log_info(
                f"/wordle: User {user.display_name} ({user.id}) won game {self._game.match_id}."
            )
            ui.update_embed_field(embed=embed, name="Status", value="You won! " + ui.EMOJIS["game_win"])
            embed.color = discord.Color.green()
        else:
            console.log_info(
                f"/wordle: User {user.display_name} ({user.id}) lost game {self._game.match_id}."
            )
            ui.update_embed_field(embed=embed, name="Status", value=f"You lost! {ui.EMOJIS['game_loss']} The secret word was '{self._game.get_secret_word()}'.")
            embed.color = discord.Color.red()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        try:
            if interaction.user.id != self._game.get_player_id():
                console.log_warning(
                    f"/wordle: Ineligible user {interaction.user.display_name} ({interaction.user.id}) "
                    f"responded to game {self._game.match_id}."
                )
                await interaction.response.send_message("You cannot respond to this game.", ephemeral=True)
                return False  # Aborts processing and DOES NOT reset/extend the view timeout

            return True  # Authorized click; allow execution
        except Exception:
            await messages.handle_error(command="/wordle", interaction=interaction, use_followup=False)
            return False

    async def on_timeout(self) -> None:
        if self._game.is_over() or self.message is None:
            return

        console.log_info(f"/wordle: Game {self._game.match_id} timed out.")
        self.disable_buttons()

        embed: discord.Embed = ui.extract_embed_from_message(message=self.message, index=0, hide_icon=True)
        ui.remove_embed_field(embed=embed, name="Timeout")
        ui.update_embed_field(
            embed=embed,
            name="Status",
            value=f"Game timed out! {ui.EMOJIS['game_timeout']} The secret word was '{self._game.get_secret_word()}'."
        )

        # Edit the original message to show disabled buttons
        await self.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Enter Guess", style=discord.ButtonStyle.primary, emoji=ui.EMOJIS["wordle_guess_button"])
    async def enter_guess_button(self, interaction: discord.Interaction, button: discord.ui.Button["WordleView"]) -> None:
        try:
            console.log_debug(
                f"/wordle: User {interaction.user.display_name} ({interaction.user.id}) "
                f"pressed the 'Enter Guess' button for game {self._game.match_id}."
            )

            assert self.message is not None
            embed: discord.Embed = ui.extract_embed_from_message(message=self.message, index=0, hide_icon=True)
            ui.update_embed_field(embed=embed, name="Timeout", value=ui.get_timeout_timestamp(self))
            await self.message.edit(embed=embed, view=self)

            modal: WordleGuessModal = WordleGuessModal(parent_view=self)
            await interaction.response.send_modal(modal)

            console.log_debug(
                f"/wordle: Modal for game {self._game.match_id} "
                f"sent to User {interaction.user.display_name} ({interaction.user.id})."
            )
        except Exception:
            await messages.handle_error(command="/wordle", interaction=interaction, use_followup=False)

    @discord.ui.button(label="Random Guess", style=discord.ButtonStyle.secondary, emoji=ui.EMOJIS["wordle_random_button"])
    async def random_guess_button(self, interaction: discord.Interaction, button: discord.ui.Button["WordleView"]) -> None:
        try:
            async def handle_random_guess(confirm_interaction: discord.Interaction) -> None:
                console.log_debug(
                    f"/wordle: User {confirm_interaction.user.display_name} ({confirm_interaction.user.id}) "
                    f"pressed the 'Random Guess' button for game {self._game.match_id}."
                )

                assert self.message is not None
                embed: discord.Embed = ui.extract_embed_from_message(message=self.message, index=0, hide_icon=True)

                random_guess: str = self._game.guess_random_word()
                console.log_info(
                    f"/wordle: User {confirm_interaction.user.display_name} ({confirm_interaction.user.id}) "
                    f"guessed random word '{random_guess}' in game {self._game.match_id}."
                )

                self.update_embed(embed=embed, user=confirm_interaction.user, default_status="Used random guess.")
                await self.message.edit(embed=embed, view=self)

            assert self.message is not None
            wordle_embed: discord.Embed = ui.extract_embed_from_message(message=self.message, index=0, hide_icon=True)
            ui.update_embed_field(embed=wordle_embed, name="Timeout", value=ui.get_timeout_timestamp(self))
            await self.message.edit(embed=wordle_embed, view=self)

            timeout: float = min(self.timeout, 30.0) if self.timeout else 30.0
            confirm_view: ui.ConfirmView = ui.ConfirmView(
                interaction=interaction,
                on_confirm=handle_random_guess,
                confirm_label="Yes",
                cancel_label="No",
                timeout=timeout
            )
            confirm_embed, confirm_icon = confirm_view.build_embed(question="Are you sure you want to use a random guess?")

            await interaction.response.send_message(embed=confirm_embed, view=confirm_view, file=confirm_icon, ephemeral=True)
        except Exception:
            await messages.handle_error(command="/wordle", interaction=interaction, use_followup=False)


class WordleGuessModal(discord.ui.Modal):
    _parent_view: WordleView

    def __init__(self, parent_view: WordleView):
        super().__init__(title="Wordle Guess")

        self._parent_view = parent_view
        console.log_debug(f"/wordle: New WordleGuessModal created for game {self._parent_view.get_game().match_id}.")

    guess_input: discord.ui.TextInput["WordleGuessModal"] = discord.ui.TextInput(
        label="Guess",
        style=discord.TextStyle.short,
        placeholder="Enter a 5-letter word",
        min_length=5,
        max_length=5,
        required=True
    )

    def _get_uncovered_guess(self) -> str:
        secret_word: str = self._parent_view.get_game().get_secret_word()
        guess: str = self.guess_input.value.lower()
        uncovered_letters: str = ""
        uncovered_colors: str = ""

        for i, letter in enumerate(guess):
            uncovered_letters += ui.EMOJIS[letter] + " "
            sw_count: int = secret_word.count(letter)

            if letter == secret_word[i]:
                uncovered_colors += ui.EMOJIS["wordle_correct_letter"] + " "
            elif letter in secret_word and guess[:i].count(letter) < sw_count and guess[i:].count(letter) <= sw_count:
                uncovered_colors += ui.EMOJIS["wordle_misplaced_letter"] + " "
            else:
                uncovered_colors += ui.EMOJIS["wordle_incorrect_letter"] + " "

        return uncovered_letters.rstrip() + "\n" + uncovered_colors.rstrip()

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            game: WordleGame = self._parent_view.get_game()
            guess: str = self.guess_input.value.lower()

            embed: discord.Embed = ui.extract_embed(interaction=interaction, index=0, hide_icon=True)

            if not game.is_valid_word(guess):
                console.log_info(
                    f"/wordle: User {interaction.user.display_name} ({interaction.user.id}) "
                    f"entered an invalid word '{guess}'."
                )

                ui.update_embed_field(embed=embed, name="Status", value=f"Entered invalid word '{guess}'.")
                await interaction.response.edit_message(embed=embed, view=self._parent_view)
                return

            if game.was_previous_guess(word=guess):
                console.log_info(
                    f"/wordle: User {interaction.user.display_name} ({interaction.user.id}) "
                    f"entered an already guesses word '{guess}'."
                )

                ui.update_embed_field(embed=embed, name="Status", value=f"You already guessed the word '{guess}'.")
                await interaction.response.edit_message(embed=embed, view=self._parent_view)
                return

            game.add_guess(word=guess)
            console.log_info(
                f"/wordle: User {interaction.user.display_name} ({interaction.user.id}) "
                f"guessed '{self.guess_input.value}' in game {self._parent_view.get_game().match_id}."
            )

            self._parent_view.update_embed(embed=embed, user=interaction.user, default_status="Valid guess.")
            await interaction.response.edit_message(embed=embed, view=self._parent_view)
            self._parent_view.message = await interaction.original_response()
        except Exception:
            await messages.handle_error(command="/wordle", interaction=interaction, use_followup=False)
