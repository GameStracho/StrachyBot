import discord

from shared import console, messages, ui

from .game import WordleGame


class WordleView(discord.ui.View):
    _game: WordleGame
    message: discord.Message | None

    def __init__(self, game: WordleGame, timeout: float = 180):
        super().__init__(timeout=timeout)

        self._game = game
        console.log_debug(f"/trivia: New WordleView created for game {self._game.match_id} with {timeout}s timeout.")

    def get_game(self) -> WordleGame:
        return self._game

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

    @discord.ui.button(label="Enter Guess", style=discord.ButtonStyle.primary, emoji=ui.EMOJIS["wordle_guess_button"])
    async def enter_guess_button(self, interaction: discord.Interaction, button: discord.ui.Button["WordleView"]) -> None:
        try:
            console.log_debug(
                f"/wordle: User {interaction.user.display_name} ({interaction.user.id}) "
                f"pressed the 'Enter Guess' button for game {self._game.match_id}."
            )

            modal: WordleGuessModal = WordleGuessModal(parent_view=self)
            await interaction.response.send_modal(modal)

            console.log_debug(
                f"/wordle: Modal for game {self._game.match_id} "
                f"sent to User {interaction.user.display_name} ({interaction.user.id})."
            )
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

            message: discord.Message | None = interaction.message
            assert message is not None

            embed: discord.Embed = message.embeds[0]
            # hide a second icon appearing above the embed
            embed.set_thumbnail(url="attachment://icon.png")

            if not game.is_valid_word(guess):
                console.log_info(
                    f"/wordle: User {interaction.user.display_name} ({interaction.user.id}) "
                    f"entered an invalid word '{guess}'."
                )

                ui.update_embed_field(embed=embed, name="Status", value=f"Entered invalid word '{guess}'.")
                await interaction.response.edit_message(embed=embed, view=self._parent_view)
                return

            if not game.guess_word(guess=guess):
                console.log_info(
                    f"/wordle: User {interaction.user.display_name} ({interaction.user.id}) "
                    f"entered an already guesses word '{guess}'."
                )

                ui.update_embed_field(embed=embed, name="Status", value=f"You already guessed the word '{guess}'.")
                await interaction.response.edit_message(embed=embed, view=self._parent_view)
                return

            console.log_info(
                f"/wordle: User {interaction.user.display_name} ({interaction.user.id}) "
                f"guessed '{self.guess_input.value}' for game {self._parent_view.get_game().match_id}."
            )

            ui.update_embed_field(embed=embed, name="Status", value="Valid guess.")

            ui.update_embed_field(embed=embed, name=f"Guess #{game.get_guesses_count()}", value=self._get_uncovered_guess())

            await interaction.response.edit_message(embed=embed, view=self._parent_view)
        except Exception:
            await messages.handle_error(command="/wordle", interaction=interaction, use_followup=False)
