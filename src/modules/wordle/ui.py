import discord

from shared import console, messages, ui

from .game import WordleGame


class WordleView(discord.ui.View):
    _game: WordleGame
    message: discord.Message | None

    def __init__(self, game: WordleGame, timeout: float = 180):
        super().__init__(timeout=timeout)

        self._game = game
        self.add_item(WordleGuessButton(self._game.match_id))

        console.log_debug(f"/trivia: New WordleView created for game {self._game.match_id} with {timeout}s timeout.")

    def get_game(self) -> WordleGame:
        return self._game


    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        try:
            if interaction.user.id != self._game.get_player_id():
                console.log_warning(
                    f"/wordle: Ineligible user {interaction.user.display_name} ({interaction.user.id}) "
                    f"responded to game {self._game.match_id}"
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


class WordleGuessButton(discord.ui.Button["WordleView"]):
    def __init__(self, game_id: int) -> None:
        super().__init__(label="Enter Guess", style=discord.ButtonStyle.primary, emoji=ui.EMOJIS["wordle_guess_button"])

        console.log_debug(f"/trivia: New WordleGuessButton created for game {game_id}.")

    async def callback(self, interaction: discord.Interaction) -> None:
        pass