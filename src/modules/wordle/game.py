import os
import random
import re
import string

from shared import console


class WordleDictionary:
    _file_path: str
    _file_size: int
    _line_size: int

    def __init__(self, file_path: str):
        self._file_path = file_path
        self._file_size = os.path.getsize(file_path)

        with open(file=file_path, mode="rb") as file:
            self._line_size = len(file.readline())

        console.log_debug(
            f"/wordle: Initialized dictionary from file '{self._file_path}' ({self._file_size} B) "
            f"with line size of {self._line_size} B"
        )

    def get_random_word(self) -> str:
        random_line: int = random.randint(a=0, b=self._file_size // self._line_size)
        result: str = ""

        with open(file=self._file_path, mode="rb") as file:
            file.seek(random_line * self._line_size)
            result = file.read(5).decode("utf-8").lower()

        console.log_debug(f"/wordle: Found random word '{result}' on line {random_line}.")
        return result

    def is_valid_word(self, word: str) -> bool:
        if len(word) != 5:
            console.log_debug(f"/wordle: Word '{word}' has invalid length {len(word)} (required 5).")
            return False

        if not word.isalpha():
            console.log_debug(f"/wordle: Word '{word}' contains invalid characters. Only letters are allowed.")
            return False

        with open(file=self._file_path, mode="rb") as file:
            low: int = 0
            high: int = self._file_size

            while low <= high:
                mid: int = (low + high) // 2
                mid -= mid % self._line_size # ensure mid is pointing to a start of a line
                file.seek(mid)

                current_word: str = file.read(5).decode("utf-8").lower()

                if current_word == word:
                    console.log_debug(f"/wordle: Word '{word}' is valid.")
                    return True
                elif current_word < word:
                    low = mid + self._line_size
                else:
                    high = mid - self._line_size

        console.log_debug(f"/wordle: Word '{word}' is invalid.")
        return False


class WordleGame:
    match_id: int
    _player_id: int
    _secret_word: str
    _guesses: list[str]
    _available_letters: set[str]
    _dictionary: WordleDictionary

    def __init__(self, player_id: int):
        self.match_id = -1
        self._player_id = player_id
        self._guesses = []
        self._available_letters = set(string.ascii_lowercase)

        module_folder: str = re.sub(pattern=r"\/[^\/]*$", repl="/", string=__file__)
        self._dictionary = WordleDictionary(file_path=module_folder + "words.txt")
        self._secret_word = self._dictionary.get_random_word()

    def __str__(self) -> str:
        return (
            f"Wordle game {self.match_id} for user {self._player_id} - {self._secret_word} (guesses: {self._guesses})"
        )

    def get_player_id(self) -> int:
        return self._player_id

    def get_secret_word(self) -> str:
        return self._secret_word

    def get_guesses_count(self) -> int:
        return len(self._guesses)

    def get_available_letters(self) -> set[str]:
        return self._available_letters

    def get_last_guess(self) -> str:
        if not len(self._guesses):
            return ""

        return self._guesses[len(self._guesses) - 1]

    def is_over(self) -> bool:
        return len(self._guesses) == 6 or (len(self._guesses) > 0 and self._guesses[len(self._guesses) -1] == self._secret_word)

    def is_valid_word(self, word: str) -> bool:
        return self._dictionary.is_valid_word(word)

    def was_previous_guess(self, word: str) -> bool:
        return word in self._guesses

    def add_guess(self, word: str) -> None:
        self._guesses.append(word)

    def guess_random_word(self) -> str:
        random_guess: str = self._dictionary.get_random_word()

        while self.was_previous_guess(random_guess):
            random_guess = self._dictionary.get_random_word()

        self._guesses.append(random_guess)
        return random_guess
