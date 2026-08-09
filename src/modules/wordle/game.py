import os
import random
import re
import string
from enum import Enum

from shared import bot, console, helpers, models

from .repository import create_match, update_match


class WordleLetterCategory(Enum):
    UNUSED = 0
    INCORRECT = 1
    MISPLACED = 2
    CORRECT = 3

    def __int__(self) -> int:
        return self.value

class WordleDictionary:
    _secret_words_path: str
    _secret_words_size: int
    _allowed_guesses_path: str
    _allowed_guesses_size: int
    _line_size: int

    def __init__(self, answers_path: str, allowed_guesses_path: str):
        self._secret_words_path = answers_path
        self._secret_words_size = os.path.getsize(answers_path)

        self._allowed_guesses_path = allowed_guesses_path
        self._allowed_guesses_size = os.path.getsize(allowed_guesses_path)

        with open(file=answers_path, mode="rb") as file:
            self._line_size = len(file.readline())

        console.log_debug(
            f"/wordle: Initialized dictionary from answers file '{self._secret_words_path}' ({self._secret_words_size} B) "
            f"and allowed guesses file '{self._allowed_guesses_path}' ({self._allowed_guesses_size} B)"
            f"with line size of {self._line_size} B"
        )

    def _get_random_word(self, file_path: str, file_size: int) -> str:
        random_line: int = random.randint(a=0, b=file_size // self._line_size)
        result: str = ""

        with open(file=file_path, mode="rb") as file:
            file.seek(random_line * self._line_size)
            result = file.read(5).decode("utf-8").lower()

        console.log_debug(f"/wordle: Found random word '{result}' on line {random_line} in file '{file_path}'.")
        return result

    def get_random_secret_word(self) -> str:
        return self._get_random_word(file_path=self._secret_words_path, file_size=self._secret_words_size)

    def get_random_allowed_guess(self) -> str:
        return self._get_random_word(file_path=self._allowed_guesses_path, file_size=self._allowed_guesses_size)

    def _find_word(self, word: str, file_path: str, file_size: int) -> bool:
        with open(file=file_path, mode="rb") as file:
            low: int = 0
            high: int = file_size

            while low <= high:
                mid: int = (low + high) // 2
                mid -= mid % self._line_size # ensure mid is pointing to a start of a line
                file.seek(mid)

                current_word: str = file.read(5).decode("utf-8").lower()

                if current_word == word:
                    return True
                elif current_word < word:
                    low = mid + self._line_size
                else:
                    high = mid - self._line_size

        return False

    def is_valid_word(self, word: str) -> bool:
        if len(word) != 5:
            console.log_debug(f"/wordle: Word '{word}' has invalid length {len(word)} (required 5).")
            return False

        if not word.isalpha():
            console.log_debug(f"/wordle: Word '{word}' contains invalid characters. Only letters are allowed.")
            return False

        if not (self._find_word(word=word, file_path=self._secret_words_path, file_size=self._secret_words_size) 
            or self._find_word(word=word, file_path=self._allowed_guesses_path, file_size=self._allowed_guesses_size)):
            console.log_debug(f"/wordle: Word '{word}' is invalid.")
            return False

        console.log_debug(f"/wordle: Word '{word}' is valid.")
        return True


class WordleGame:
    _bot: bot.StrachyBot | None
    match_id: int
    _status: models.EMatchStatus
    _player_id: int
    _secret_word: str
    _guesses: list[str]
    _available_letters: dict[str, WordleLetterCategory]
    _dictionary: WordleDictionary

    def __init__(self, player_id: int) -> None:
        self._bot = None
        self.match_id = -1
        self._player_id = player_id
        self._guesses = []
        self._status = models.EMatchStatus.PENDING

        self._available_letters = {}

        for letter in string.ascii_lowercase:
            self._available_letters[letter] = WordleLetterCategory.UNUSED

        module_folder: str = re.sub(pattern=r"\/[^\/]*$", repl="/", string=__file__)
        self._dictionary = WordleDictionary(
            answers_path=module_folder + "secret-words.txt",
            allowed_guesses_path=module_folder + "allowed-guesses.txt"
        )
        self._secret_word = self._dictionary.get_random_secret_word()

    def __str__(self) -> str:
        return (
            f"Wordle game {self.match_id} for user {self._player_id} - {self._secret_word} (guesses: {self._guesses})"
        )

    async def _update_database_record(self) -> None:
        if not self._bot:
            return

        await helpers.execute_db_operation(
            target=self._bot, db_func=update_match,
            match_id=self.match_id, status=self._status, guesses=len(self._guesses)
        )

    def get_player_id(self) -> int:
        return self._player_id

    def get_secret_word(self) -> str:
        return self._secret_word

    def get_guesses_count(self) -> int:
        return len(self._guesses)

    def get_available_letters(self) -> dict[str, WordleLetterCategory]:
        return self._available_letters

    def get_last_guess(self) -> str:
        if not len(self._guesses):
            return ""

        return self._guesses[len(self._guesses) - 1]

    def get_status(self) -> models.EMatchStatus:
        return self._status

    def is_valid_word(self, word: str) -> bool:
        return self._dictionary.is_valid_word(word)

    def is_previous_guess(self, word: str) -> bool:
        return word in self._guesses

    async def connect_database(self, bot: bot.StrachyBot) -> None:
        self._bot = bot

        match_id: int | None = await helpers.execute_db_operation(
            target=self._bot, db_func=create_match,
            player_id=self._player_id,
            secret_word=self._secret_word
        )

        if match_id:
            self.match_id = match_id

    async def add_guess(self, word: str) -> None:
        if self._status != models.EMatchStatus.PENDING:
            return

        self._guesses.append(word)
        console.log_info(f"/wordle: User '{self._player_id}' guessed word '{word}' in game {self.match_id}.")

        if word == self._secret_word:
            console.log_info(f"/wordle: User '{self._player_id}' won game {self.match_id}.")
            self._status = models.EMatchStatus.WIN
            await self._update_database_record()
            return

        if len(self._guesses) == 6:
            console.log_info(
                f"/wordle: User '{self._player_id}' lost game {self.match_id}."
            )
            self._status = models.EMatchStatus.LOSS
            await self._update_database_record()

    async def guess_random_word(self) -> None:
        random_guess: str = self._dictionary.get_random_allowed_guess()

        while self.is_previous_guess(random_guess):
            random_guess = self._dictionary.get_random_allowed_guess()

        console.log_info(f"/wordle: generated random word '{random_guess}' for game {self.match_id}")

        await self.add_guess(word=random_guess)

    async def handle_timeout(self) -> None:
        if self._status != models.EMatchStatus.PENDING:
            return

        console.log_info(f"/wordle: Game {self.match_id} timed out.")
        self._status = models.EMatchStatus.TIMEOUT
        await self._update_database_record()

    async def handle_surrender(self) -> None:
        if self._status != models.EMatchStatus.PENDING:
                    return
        
        console.log_info(f"/wordle: Player '{self._player_id}' gave up game {self.match_id}.")
        self._status = models.EMatchStatus.SURRENDER
        await self._update_database_record()

    def categorize_word(self, word: str) -> list[tuple[str, WordleLetterCategory]]:
        """
            Categorizes each letter of the word based on the it's position relative to the secret word
            and updates the categories of available letters.

            Returns each letter of the word with it's categorization
        """
        result: list[tuple[str, WordleLetterCategory]] = []

        for i, letter in enumerate(word):
            sw_count: int = self._secret_word.count(letter)
            category: WordleLetterCategory = WordleLetterCategory.INCORRECT

            if letter == self._secret_word[i]:
                category = WordleLetterCategory.CORRECT
            elif letter in self._secret_word and word[:i].count(letter) < sw_count and word[i:].count(letter) <= sw_count:
                category = WordleLetterCategory.MISPLACED

            result.append((letter, category))

            if int(category) > int(self._available_letters[letter]):
                self._available_letters[letter] = category

        return result