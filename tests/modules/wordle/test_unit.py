import re
from datetime import date
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

import modules.wordle.game as game_mod
from modules.wordle.game import WordleDictionary, WordleGame, WordleLetterCategory
from modules.wordle.ui import WordleGuessModal, WordleView
from shared import models, ui
from tests import mocks


@pytest.mark.parametrize(
    ("category", "expected_int"),
    [
        (WordleLetterCategory.UNUSED, 0),
        (WordleLetterCategory.INCORRECT, 1),
        (WordleLetterCategory.MISPLACED, 2),
        (WordleLetterCategory.CORRECT, 3),
    ],
)
def test_wordle_letter_category_int(category: WordleLetterCategory, expected_int: int) -> None:
    assert int(category) == expected_int


def test_wordle_dictionary_initialization() -> None:
    # Find the real files
    module_folder = re.sub(pattern=r"\/[^\/]*$", repl="/", string=game_mod.__file__)
    answers_path = module_folder + "secret-words.txt"
    guesses_path = module_folder + "allowed-guesses.txt"

    dictionary = WordleDictionary(answers_path=answers_path, allowed_guesses_path=guesses_path)

    assert dictionary._line_size == 6
    assert dictionary._secret_words_size > 0
    assert dictionary._allowed_guesses_size > 0


def test_wordle_dictionary_validation() -> None:
    module_folder = re.sub(pattern=r"\/[^\/]*$", repl="/", string=game_mod.__file__)
    answers_path = module_folder + "secret-words.txt"
    guesses_path = module_folder + "allowed-guesses.txt"

    dictionary = WordleDictionary(answers_path=answers_path, allowed_guesses_path=guesses_path)

    # Valid secret word
    assert dictionary.is_valid_word("aback") is True
    # Valid allowed guess
    assert dictionary.is_valid_word("aahed") is True
    # Invalid length
    assert dictionary.is_valid_word("invalid") is False
    # Non-alpha
    assert dictionary.is_valid_word("12345") is False
    # Not in lists
    assert dictionary.is_valid_word("xxxxx") is False


def test_wordle_dictionary_random_selections() -> None:
    module_folder = re.sub(pattern=r"\/[^\/]*$", repl="/", string=game_mod.__file__)
    answers_path = module_folder + "secret-words.txt"
    guesses_path = module_folder + "allowed-guesses.txt"

    dictionary = WordleDictionary(answers_path=answers_path, allowed_guesses_path=guesses_path)

    secret = dictionary.get_random_secret_word()
    assert len(secret) == 5
    assert dictionary.is_valid_word(secret) is True

    guess = dictionary.get_random_allowed_guess()
    assert len(guess) == 5
    assert dictionary.is_valid_word(guess) is True


def test_wordle_dictionary_daily_secret_word() -> None:
    module_folder = re.sub(pattern=r"\/[^\/]*$", repl="/", string=game_mod.__file__)
    answers_path = module_folder + "secret-words.txt"
    guesses_path = module_folder + "allowed-guesses.txt"

    dictionary = WordleDictionary(answers_path=answers_path, allowed_guesses_path=guesses_path)

    # Calling with same date should be deterministic
    d = date(2026, 8, 9)
    w1 = dictionary.get_daily_secret_word(d)
    w2 = dictionary.get_daily_secret_word(d)
    assert w1 == w2
    assert len(w1) == 5

    # Different date should return a different word (usually)
    d2 = date(2026, 8, 10)
    w3 = dictionary.get_daily_secret_word(d2)
    assert w1 != w3

    # Calling without target date runs
    w4 = dictionary.get_daily_secret_word()
    assert len(w4) == 5


def test_wordle_game_initialization() -> None:
    game = WordleGame(player_id=123, is_daily=False)
    assert game.get_player_id() == 123
    assert game.is_daily() is False
    assert game.get_match_id() == -1
    assert game.get_status() == models.EMatchStatus.PENDING
    assert game.get_guesses_count() == 0
    assert game.get_last_guess() == ""
    assert len(game.get_secret_word()) == 5
    assert "Wordle game" in str(game)


@pytest.mark.asyncio
async def test_wordle_game_connect_database(monkeypatch: pytest.MonkeyPatch) -> None:
    game = WordleGame(player_id=123, is_daily=False)
    bot_mock = mocks.DummyStrachyBot()

    async def mock_execute(*args: Any, **kwargs: Any) -> int:
        return 999

    monkeypatch.setattr("modules.wordle.game.execute_db_operation", mock_execute)

    await game.connect_database(bot_mock)
    assert game.get_match_id() == 999


@pytest.mark.asyncio
async def test_wordle_game_add_guess_win(monkeypatch: pytest.MonkeyPatch) -> None:
    game = WordleGame(player_id=123, is_daily=False)
    game._secret_word = "apple"
    bot_mock = mocks.DummyStrachyBot()
    game._bot = bot_mock
    game._match_id = 999

    update_mock = AsyncMock()
    monkeypatch.setattr("modules.wordle.game.execute_db_operation", update_mock)

    await game.add_guess("apple")

    assert game.get_guesses_count() == 1
    assert game.get_last_guess() == "apple"
    assert game.get_status() == models.EMatchStatus.WIN
    update_mock.assert_called_once()


@pytest.mark.asyncio
async def test_wordle_game_add_guess_loss(monkeypatch: pytest.MonkeyPatch) -> None:
    game = WordleGame(player_id=123, is_daily=False)
    game._secret_word = "apple"
    bot_mock = mocks.DummyStrachyBot()
    game._bot = bot_mock
    game._match_id = 999

    update_mock = AsyncMock()
    monkeypatch.setattr("modules.wordle.game.execute_db_operation", update_mock)

    # 5 wrong guesses
    for _ in range(5):
        await game.add_guess("pears")
        assert game.get_status() == models.EMatchStatus.PENDING

    # 6th wrong guess triggers LOSS
    await game.add_guess("pears")
    assert game.get_status() == models.EMatchStatus.LOSS
    assert game.get_guesses_count() == 6
    update_mock.assert_called_once()


@pytest.mark.asyncio
async def test_wordle_game_add_guess_not_pending() -> None:
    game = WordleGame(player_id=123, is_daily=False)
    game._secret_word = "apple"
    game._status = models.EMatchStatus.WIN

    await game.add_guess("pears")
    # Guess should be ignored
    assert game.get_guesses_count() == 0


@pytest.mark.asyncio
async def test_wordle_game_guess_random_word(monkeypatch: pytest.MonkeyPatch) -> None:
    game = WordleGame(player_id=123, is_daily=False)
    game._secret_word = "apple"

    call_count = 0

    def mock_get_random(*args: Any) -> str:
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            return "pears"
        return "about"

    monkeypatch.setattr(game._dictionary, "get_random_allowed_guess", mock_get_random)

    # Add "pears" as previous guess to trigger the duplicate check loop
    game._guesses = ["pears"]

    await game.guess_random_word()
    assert game.get_guesses_count() == 2
    assert game.get_last_guess() == "about"


@pytest.mark.asyncio
async def test_wordle_game_handle_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    game = WordleGame(player_id=123, is_daily=False)
    bot_mock = mocks.DummyStrachyBot()
    game._bot = bot_mock
    game._match_id = 999

    update_mock = AsyncMock()
    monkeypatch.setattr("modules.wordle.game.execute_db_operation", update_mock)

    await game.handle_timeout()
    assert game.get_status() == models.EMatchStatus.TIMEOUT
    update_mock.assert_called_once()

    # Call it again when not pending, it should do nothing
    update_mock.reset_mock()
    await game.handle_timeout()
    update_mock.assert_not_called()


@pytest.mark.asyncio
async def test_wordle_game_handle_surrender(monkeypatch: pytest.MonkeyPatch) -> None:
    game = WordleGame(player_id=123, is_daily=False)
    bot_mock = mocks.DummyStrachyBot()
    game._bot = bot_mock
    game._match_id = 999

    update_mock = AsyncMock()
    monkeypatch.setattr("modules.wordle.game.execute_db_operation", update_mock)

    await game.handle_surrender()
    assert game.get_status() == models.EMatchStatus.SURRENDER
    update_mock.assert_called_once()

    # Call it again when not pending, it should do nothing
    update_mock.reset_mock()
    await game.handle_surrender()
    update_mock.assert_not_called()


def test_wordle_game_categorize_word() -> None:
    game = WordleGame(player_id=123, is_daily=False)
    game._secret_word = "apple"

    # Some misplaced, some incorrect
    res1 = game.categorize_word("pears")
    assert res1 == [
        ("p", WordleLetterCategory.MISPLACED),
        ("e", WordleLetterCategory.MISPLACED),
        ("a", WordleLetterCategory.MISPLACED),
        ("r", WordleLetterCategory.INCORRECT),
        ("s", WordleLetterCategory.INCORRECT),
    ]

    # Verify available letters updates
    avail = game.get_available_letters()
    assert avail["p"] == WordleLetterCategory.MISPLACED
    assert avail["e"] == WordleLetterCategory.MISPLACED
    assert avail["a"] == WordleLetterCategory.MISPLACED
    assert avail["r"] == WordleLetterCategory.INCORRECT
    assert avail["s"] == WordleLetterCategory.INCORRECT
    assert avail["z"] == WordleLetterCategory.UNUSED

    # Double letter count check (Guess has three p's: 'paper')
    res2 = game.categorize_word("paper")
    assert res2 == [
        ("p", WordleLetterCategory.MISPLACED),
        ("a", WordleLetterCategory.MISPLACED),
        ("p", WordleLetterCategory.CORRECT),
        ("e", WordleLetterCategory.MISPLACED),
        ("r", WordleLetterCategory.INCORRECT),
    ]

    # Verify available letters updates
    avail = game.get_available_letters()
    assert avail["p"] == WordleLetterCategory.CORRECT
    assert avail["e"] == WordleLetterCategory.MISPLACED
    assert avail["a"] == WordleLetterCategory.MISPLACED
    assert avail["r"] == WordleLetterCategory.INCORRECT
    assert avail["s"] == WordleLetterCategory.INCORRECT
    assert avail["z"] == WordleLetterCategory.UNUSED

    # Exact match
    res3 = game.categorize_word("apple")
    assert res3 == [
        ("a", WordleLetterCategory.CORRECT),
        ("p", WordleLetterCategory.CORRECT),
        ("p", WordleLetterCategory.CORRECT),
        ("l", WordleLetterCategory.CORRECT),
        ("e", WordleLetterCategory.CORRECT),
    ]

    # Verify available letters updates
    avail = game.get_available_letters()
    assert avail["p"] == WordleLetterCategory.CORRECT
    assert avail["e"] == WordleLetterCategory.CORRECT
    assert avail["a"] == WordleLetterCategory.CORRECT
    assert avail["r"] == WordleLetterCategory.INCORRECT
    assert avail["s"] == WordleLetterCategory.INCORRECT
    assert avail["z"] == WordleLetterCategory.UNUSED


def test_wordle_view_build_embed() -> None:
    game = WordleGame(player_id=123, is_daily=False)
    view = WordleView(game=game)
    user = mocks.create_dummy_user(123, "Alice")

    embed, file = view.build_embed(user)
    assert embed.title == "Wordle"
    assert embed.author.name == "Alice"
    assert len(embed.fields) == 9
    assert file.filename == "icon.png"

    # Daily challenge title contains date
    game_daily = WordleGame(player_id=123, is_daily=True)
    view_daily = WordleView(game=game_daily)
    embed_daily, _ = view_daily.build_embed(user)
    assert "Wordle 20" in cast(str, embed_daily.title)


def test_wordle_view_disable_buttons() -> None:
    game = WordleGame(player_id=123, is_daily=False)
    view = WordleView(game=game)

    for child in view.children:
        if isinstance(child, discord.ui.Button):
            assert child.disabled is False

    view.disable_buttons()

    for child in view.children:
        if isinstance(child, discord.ui.Button):
            assert child.disabled is True


def test_wordle_view_get_letter_category_emoji() -> None:
    game = WordleGame(player_id=123, is_daily=False)
    view = WordleView(game=game)

    assert view._get_letter_category_emoji(WordleLetterCategory.CORRECT) is not None
    assert view._get_letter_category_emoji(WordleLetterCategory.MISPLACED) is not None
    assert view._get_letter_category_emoji(WordleLetterCategory.INCORRECT) is not None
    assert view._get_letter_category_emoji(WordleLetterCategory.UNUSED) is not None

    with pytest.raises(ValueError):
        view._get_letter_category_emoji(cast(WordleLetterCategory, -1))


def test_wordle_view_uncover_word() -> None:
    game = WordleGame(player_id=123, is_daily=False)
    game._secret_word = "apple"
    view = WordleView(game=game)

    val = view._uncover_word("apple")
    assert val is not None

    # Spoiler wrapping for daily
    game_daily = WordleGame(player_id=123, is_daily=True)
    game_daily._secret_word = "apple"
    view_daily = WordleView(game=game_daily)
    val_daily = view_daily._uncover_word("apple")
    assert val_daily.startswith("||")


def test_wordle_view_update_embed() -> None:
    game = WordleGame(player_id=123, is_daily=False)
    game._secret_word = "apple"
    view = WordleView(game=game)

    embed = discord.Embed(title="Wordle")
    embed.add_field(name="Guess #1", value="empty")
    embed.add_field(name="Used letters", value="empty")
    embed.add_field(name="Status", value="empty")
    embed.add_field(name="Timeout", value="empty")

    # 1. PENDING
    game._guesses = ["apple"]
    view.update_embed(embed, "Keep playing")
    assert any(field.name == "Timeout" for field in embed.fields)

    # 2. WIN
    game._status = models.EMatchStatus.WIN
    view.update_embed(embed, "Won")
    assert embed.color == discord.Color.green()
    assert not any(field.name == "Timeout" for field in embed.fields)

    # 3. LOSS
    embed2 = discord.Embed(title="Wordle")
    embed2.add_field(name="Guess #1", value="empty")
    embed2.add_field(name="Used letters", value="empty")
    embed2.add_field(name="Status", value="empty")
    embed2.add_field(name="Timeout", value="empty")

    game._status = models.EMatchStatus.LOSS
    view2 = WordleView(game=game)
    view2.update_embed(embed2, "Lost")
    assert embed2.color == discord.Color.red()

    # 4. SURRENDER
    embed3 = discord.Embed(title="Wordle")
    embed3.add_field(name="Guess #1", value="empty")
    embed3.add_field(name="Used letters", value="empty")
    embed3.add_field(name="Status", value="empty")
    embed3.add_field(name="Timeout", value="empty")

    game._status = models.EMatchStatus.SURRENDER
    view3 = WordleView(game=game)
    view3.update_embed(embed3, "Gave up")
    assert embed3.color == ui.COLORS["white"]

    # 5. Invalid Status
    game._status = models.EMatchStatus.TIMEOUT
    view4 = WordleView(game=game)
    with pytest.raises(ValueError):
        view4.update_embed(embed3, "Error")


@pytest.mark.asyncio
async def test_wordle_view_interaction_check(monkeypatch: pytest.MonkeyPatch) -> None:
    game = WordleGame(player_id=123, is_daily=False)
    view = WordleView(game=game)

    # Eligible
    interaction_valid = mocks.DummyInteraction(user_id=123, username="Alice")
    assert await view.interaction_check(interaction_valid) is True

    # Ineligible
    interaction_invalid = mocks.DummyInteraction(user_id=456, username="Bob")
    assert await view.interaction_check(interaction_invalid) is False
    assert interaction_invalid.response.send_message.called

    # Exception
    monkeypatch.setattr(game, "get_player_id", MagicMock(side_effect=Exception("Failed")))
    error_mock = AsyncMock()
    monkeypatch.setattr("modules.wordle.ui.ui.handle_error", error_mock)

    interaction_err = mocks.DummyInteraction(user_id=123, username="Alice")
    assert await view.interaction_check(interaction_err) is False
    error_mock.assert_called_once()


@pytest.mark.asyncio
async def test_wordle_view_on_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    game = WordleGame(player_id=123, is_daily=False)
    game._secret_word = "apple"
    view = WordleView(game=game)

    # Message is None
    view.message = None
    await view.on_timeout()
    assert game.get_status() == models.EMatchStatus.PENDING

    # Game is WIN (not PENDING)
    game._status = models.EMatchStatus.WIN
    message_mock = AsyncMock()
    view.message = message_mock
    await view.on_timeout()
    assert game.get_status() == models.EMatchStatus.WIN
    message_mock.edit.assert_not_called()

    # Normal timeout path
    game._status = models.EMatchStatus.PENDING
    embed = discord.Embed(title="Wordle")
    embed.add_field(name="Timeout", value="active")
    embed.add_field(name="Status", value="active")

    message_mock = AsyncMock()
    message_mock.embeds = [embed]
    view.message = message_mock

    update_mock = AsyncMock()
    monkeypatch.setattr("modules.wordle.game.execute_db_operation", update_mock)

    await view.on_timeout()

    assert game.get_status() == models.EMatchStatus.TIMEOUT
    assert not any(field.name == "Timeout" for field in embed.fields)
    message_mock.edit.assert_called_once()


@pytest.mark.asyncio
async def test_wordle_view_enter_guess_button(monkeypatch: pytest.MonkeyPatch) -> None:
    game = WordleGame(player_id=123, is_daily=False)
    view = WordleView(game=game)

    embed = discord.Embed(title="Wordle")
    embed.add_field(name="Timeout", value="active")
    message_mock = AsyncMock()
    message_mock.embeds = [embed]
    view.message = message_mock

    interaction = mocks.DummyInteraction(user_id=123, username="Alice")

    # Happy path
    callback = view.enter_guess_button.callback
    assert callback is not None
    await callback(interaction)
    assert message_mock.edit.called
    assert interaction.response.send_modal.called

    # Exception path
    error_mock = AsyncMock()
    monkeypatch.setattr("modules.wordle.ui.ui.handle_error", error_mock)
    message_mock.edit.side_effect = Exception("Failed")
    callback_err = view.enter_guess_button.callback
    assert callback_err is not None
    await callback_err(interaction)
    error_mock.assert_called_once()


@pytest.mark.asyncio
async def test_wordle_view_random_guess_button(monkeypatch: pytest.MonkeyPatch) -> None:
    game = WordleGame(player_id=123, is_daily=False)
    view = WordleView(game=game)

    embed = discord.Embed(title="Wordle")
    embed.add_field(name="Timeout", value="active")
    message_mock = AsyncMock()
    message_mock.embeds = [embed]
    view.message = message_mock

    interaction = mocks.DummyInteraction(user_id=123, username="Alice")

    confirm_view_inst = None
    original_init = ui.ConfirmView.__init__

    def mock_confirm_init(self: Any, *args: Any, **kwargs: Any) -> None:
        nonlocal confirm_view_inst
        original_init(self, *args, **kwargs)
        confirm_view_inst = self

    monkeypatch.setattr(ui.ConfirmView, "__init__", mock_confirm_init)

    callback = view.random_guess_button.callback
    assert callback is not None
    await callback(interaction)

    assert message_mock.edit.called
    assert interaction.response.send_message.called
    assert confirm_view_inst is not None

    # Trigger confirm callback
    guess_mock = AsyncMock()
    monkeypatch.setattr(game, "guess_random_word", guess_mock)

    confirm_interaction = mocks.DummyInteraction(user_id=123, username="Alice")
    confirm_interaction.message = message_mock

    await confirm_view_inst._on_confirm(confirm_interaction)

    guess_mock.assert_called_once()
    assert message_mock.edit.call_count >= 2

    # Exception path
    error_mock = AsyncMock()
    monkeypatch.setattr("modules.wordle.ui.ui.handle_error", error_mock)
    view.message = None
    callback_err = view.random_guess_button.callback
    assert callback_err is not None
    await callback_err(interaction)
    error_mock.assert_called_once()


@pytest.mark.asyncio
async def test_wordle_view_give_up_button(monkeypatch: pytest.MonkeyPatch) -> None:
    game = WordleGame(player_id=123, is_daily=False)
    view = WordleView(game=game)

    embed = discord.Embed(title="Wordle")
    embed.add_field(name="Timeout", value="active")
    message_mock = AsyncMock()
    message_mock.embeds = [embed]
    view.message = message_mock

    interaction = mocks.DummyInteraction(user_id=123, username="Alice")

    confirm_view_inst = None
    original_init = ui.ConfirmView.__init__

    def mock_confirm_init(self: Any, *args: Any, **kwargs: Any) -> None:
        nonlocal confirm_view_inst
        original_init(self, *args, **kwargs)
        confirm_view_inst = self

    monkeypatch.setattr(ui.ConfirmView, "__init__", mock_confirm_init)

    callback = view.give_up_button.callback
    assert callback is not None
    await callback(interaction)

    assert message_mock.edit.called
    assert interaction.response.send_message.called
    assert confirm_view_inst is not None

    # Trigger confirm callback
    surrender_mock = AsyncMock()
    monkeypatch.setattr(game, "handle_surrender", surrender_mock)

    confirm_interaction = mocks.DummyInteraction(user_id=123, username="Alice")
    confirm_interaction.message = message_mock

    await confirm_view_inst._on_confirm(confirm_interaction)

    surrender_mock.assert_called_once()
    assert message_mock.edit.call_count >= 2

    # Exception path
    error_mock = AsyncMock()
    monkeypatch.setattr("modules.wordle.ui.ui.handle_error", error_mock)
    view.message = None
    callback_err = view.give_up_button.callback
    assert callback_err is not None
    await callback_err(interaction)
    error_mock.assert_called_once()


def test_wordle_guess_modal_get_uncovered_guess() -> None:
    game = WordleGame(player_id=123, is_daily=False)
    game._secret_word = "apple"
    view = WordleView(game=game)
    modal = WordleGuessModal(parent_view=view)
    cast(Any, modal.guess_input)._value = "pears"

    val = modal._get_uncovered_guess()
    assert val is not None


@pytest.mark.asyncio
async def test_wordle_guess_modal_on_submit(monkeypatch: pytest.MonkeyPatch) -> None:
    game = WordleGame(player_id=123, is_daily=False)
    game._secret_word = "apple"
    view = WordleView(game=game)

    embed = discord.Embed(title="Wordle")
    embed.add_field(name="Status", value="active")
    interaction = mocks.DummyInteraction(user_id=123, username="Alice")
    interaction.user = mocks.create_dummy_user(123, "Alice")

    monkeypatch.setattr("modules.wordle.ui.ui.embed.extract", lambda *args, **kwargs: embed)

    # 1. Invalid word path
    modal = WordleGuessModal(parent_view=view)
    cast(Any, modal.guess_input)._value = "xxxxx"
    await modal.on_submit(interaction)
    assert "invalid word" in cast(str, embed.fields[0].value)
    assert interaction.response.edit_message.called

    interaction.response.edit_message.reset_mock()

    # 2. Already guessed path
    game._guesses = ["pears"]
    modal2 = WordleGuessModal(parent_view=view)
    cast(Any, modal2.guess_input)._value = "pears"
    await modal2.on_submit(interaction)
    assert "already guessed" in cast(str, embed.fields[0].value)
    assert interaction.response.edit_message.called

    interaction.response.edit_message.reset_mock()

    # 3. Valid guess path
    game._guesses = []
    add_guess_mock = AsyncMock()
    monkeypatch.setattr(game, "add_guess", add_guess_mock)

    msg_mock = AsyncMock()
    monkeypatch.setattr(interaction, "original_response", AsyncMock(return_value=msg_mock))

    modal3 = WordleGuessModal(parent_view=view)
    cast(Any, modal3.guess_input)._value = "pears"
    await modal3.on_submit(interaction)

    add_guess_mock.assert_called_once_with(word="pears")
    assert interaction.response.edit_message.called
    assert view.message == msg_mock

    # 4. Exception path
    error_mock = AsyncMock()
    monkeypatch.setattr("modules.wordle.ui.ui.handle_error", error_mock)
    monkeypatch.setattr(
        "modules.wordle.ui.ui.embed.extract", MagicMock(side_effect=Exception("Failed"))
    )
    await modal3.on_submit(interaction)
    error_mock.assert_called_once()
