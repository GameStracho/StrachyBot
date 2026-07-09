import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

# connect /src directory
ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from shared import database
from shared.bot import StrachyBot
from shared.database import Base


class _DummyConnection:
    async def run_sync(self, _func):
        return None


class _DummyTransaction:
    async def __aenter__(self):
        return _DummyConnection()

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _dummy_begin():
    return _DummyTransaction()


@pytest.mark.asyncio
async def test_all_modules_load_and_sync_correctly(monkeypatch):
    # 1. Arrange: Find out how many actual folders exist in /src/modules
    modules_dir = ROOT / "src" / "modules"
    expected_modules = [
        folder for folder in os.listdir(modules_dir)
        if os.path.isdir(os.path.join(modules_dir, folder)) and "__init__.py" in os.listdir(os.path.join(modules_dir, folder))
    ]

    # Mock the database engine
    monkeypatch.setattr(database, "engine", type("EngineStub", (), {"begin": lambda self: _DummyTransaction()})())

    # 2. Act: Instantiate the bot and run custom dynamic setup hook
    bot = StrachyBot()
    monkeypatch.setattr(bot.tree, "sync", AsyncMock(return_value=[]))
    await bot.setup_hook()

    # 3. Assert: Verify all Cogs loaded correctly into discord.py
    loaded_cogs = list(bot.cogs.keys())
    print(f"Loaded cogs found: {loaded_cogs}")

    # Ensure the number of loaded cogs matches the number of module folders
    # (Assuming every module folder loads exactly 1 Cog class)
    assert len(loaded_cogs) == len(expected_modules), (
        f"Mismatch! Found {len(expected_modules)} module folders, but only {len(loaded_cogs)} cogs loaded."
    )

    # 4. Assert: Verify SQLAlchemy successfully mapped all database models
    # Base.metadata.tables is a dictionary of all registered tables in memory
    registered_tables = Base.metadata.tables.keys()
    print(f"Registered tables found: {list(registered_tables)}")
    
    # Verify core table exists
    assert "match_history" in registered_tables, "Core 'match_history' table was not registered!"
    
    # Check that module-specific tables were discovered dynamically
    for module in expected_modules:
        if module == "wordle":
            assert "wordle_match" in registered_tables, "Wordle database models failed to sync!"
        elif module == "tic_tac_toe":
            assert "tic_tac_toe_match" in registered_tables, "Tic-Tac-Toe database models failed to sync!"

    # Clean up bot connection resources
    await bot.close()