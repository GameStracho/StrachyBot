import os
from unittest.mock import AsyncMock

import pytest

from shared.bot import StrachyBot
from shared.database import Base
from tests import mocks


@pytest.mark.asyncio
async def test_all_modules_load_and_sync_correctly(monkeypatch: pytest.MonkeyPatch) -> None:
    # 1. Arrange: Find out how many actual folders exist in /src/modules
    modules_dir = os.path.join(os.path.dirname(__file__), "..", "..", "src", "modules")
    expected_modules = [
        folder
        for folder in os.listdir(modules_dir)
        if os.path.isdir(os.path.join(modules_dir, folder))
        and "__init__.py" in os.listdir(os.path.join(modules_dir, folder))
    ]

    # 2. Act: Instantiate the bot and run custom dynamic setup hook
    mock_engine = type(
        "EngineStub", (), {"begin": lambda self: mocks.DummyTransaction(), "dispose": AsyncMock()}
    )()
    bot = StrachyBot()
    bot.create_db_session_factory(mock_engine)
    monkeypatch.setattr(bot.tree, "sync", AsyncMock(return_value=[]))
    await bot.setup_hook()

    # 3. Assert: Verify all Cogs loaded correctly into discord.py
    loaded_cogs = list(bot.cogs.keys())
    print(f"Loaded cogs found: {loaded_cogs}")

    # Ensure the number of loaded cogs matches the number of module folders
    # (Assuming every module folder loads exactly 1 Cog class)
    assert len(loaded_cogs) == len(expected_modules), (
        f"Mismatch! Found {len(expected_modules)} module folders, "
        f"but only {len(loaded_cogs)} cogs loaded."
    )

    # 4. Assert: Verify SQLAlchemy successfully mapped all database models
    # Base.metadata.tables is a dictionary of all registered tables in memory
    registered_tables = Base.metadata.tables.keys()
    print(f"Registered tables found: {list(registered_tables)}")

    # Verify core table exists
    assert "match" in registered_tables, "Core 'match' table was not registered!"

    # Check that module-specific tables were discovered dynamically
    for module in expected_modules:
        if module == "wordle":
            assert "wordle_match" in registered_tables, "Wordle database models failed to sync!"
        elif module == "tic_tac_toe":
            assert "tic_tac_toe_match" in registered_tables, (
                "Tic-Tac-Toe database models failed to sync!"
            )

    # Clean up bot connection resources
    await bot.close()
