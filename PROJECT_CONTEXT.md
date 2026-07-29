# 🤖 StrachyBot - Project Context & Developer Reference

This document provides a comprehensive overview of the **StrachyBot** codebase, its architecture, core components, data models, developer conventions, and operational workflows.

---

## 📌 Project Overview

**StrachyBot** is a modular Discord bot built with **Python 3.11+**, **discord.py (v2.3+)**, and **SQLAlchemy 2.0 (Async)** backed by a **PostgreSQL 15** database. It features interactive mini-games (*Tic-Tac-Toe*, *Wordle*, *Trivia*), utility tools, slash command integrations, and automated database backups.

---

## 🏗️ Technical Architecture & Key Patterns

### 1. Modular Cog Architecture
- **Dynamic Module Loading**: The custom bot class `StrachyBot` (in `src/shared/bot.py`) dynamically scans `src/modules/` during setup.
- **Module Requirements**: A directory in `src/modules/` is loaded as a bot extension if it contains a `cogs.py` file. If `models.py` is present in the module, its database models are registered automatically.
- **Slash Commands**: Handled via `discord.app_commands`. Command trees are synced with Discord upon bot startup.

### 2. Async Database Infrastructure
- **ORM & Driver**: Uses SQLAlchemy 2.0 async ORM with `asyncpg`.
- **Session Factory**: Created during bot initialization (`bot.create_db_session_factory()`).
- **Database Operations**: Database interactions are routed asynchronously using `shared.helpers.execute_db_operation()` to ensure safe session management and context scope.
- **Migrations**: Database schema changes are managed via **Alembic** (`alembic.ini` and `migrations/`).

### 3. Shared Core (`src/shared/`)
- `bot.py`: Subclasses `commands.Bot`; initializes database engines, dynamically loads cogs/models, and syncs command trees.
- `database.py`: Defines the async engine creator, `async_sessionmaker`, and the SQLAlchemy `Base` declarative base class.
- `models.py`: Shared database models (e.g., base `Match` table, `EMatchStatus` enum) and common exceptions (`NoAPIResponseException`).
- `helpers.py`: Utility helper for executing DB transactions (`execute_db_operation`) and loading discord asset attachments.
- `console.py`: Colorized logging framework built with `colorama`.
- `messages.py`: Standardized error handling and user notification wrappers.
- `ui.py`: UI helpers for Discord components (e.g., dynamic timestamp formatting).

---

## 📁 Repository Directory Map

```
StrachyBot/
├── .github/                      # GitHub workflow & CI configurations
├── backups/                      # Backup repository target directory (cloned private repo)
├── migrations/                   # Alembic database migration scripts & versions
│   └── versions/                 # Revision scripts (e.g. initial_schema, add_trivia_models)
├── scripts/                      # Utility scripts
│   └── backup.sh                 # Cron script for dumping Postgres DB & committing to Git
├── src/                          # Main application source code
│   ├── main.py                   # Application entry point
│   ├── cz_words.txt              # Czech word dictionary for Wordle
│   ├── wordle-words.txt          # Wordle target words dictionary
│   ├── words.txt                 # English word dictionary
│   ├── emojis.json               # Custom emoji definitions
│   ├── stats.json / user_data.json # Data storage files
│   ├── modules/                  # Modular feature extensions
│   │   ├── google.py             # Google API Integration / authentication helpers
│   │   ├── stats.py              # Statistics tracking module
│   │   ├── tic_tac_toe/          # Tic-Tac-Toe mini-game module (cogs, game logic, UI, repo)
│   │   ├── trivia/               # Trivia mini-game module (Open Trivia DB API integration)
│   │   ├── utils/                # General utilities (/info, /announcement)
│   │   └── wordle/               # Wordle mini-game module
│   └── shared/                   # Core shared system components & helpers
├── tests/                        # Pytest suite
│   ├── shared/                   # Shared module tests (bot loading, etc.)
│   └── modules/                  # Feature module unit & integration tests
├── .env.example                  # Environment configuration template
├── docker-compose.yml            # Docker stack configuration (Postgres, Socat, Adminer, Bot)
├── Dockerfile                    # Container definition for production bot runtime
├── pyproject.toml                # Project settings, Pytest & Ruff linter configuration
├── requirements.txt              # Production Python dependencies
├── requirements-dev.txt          # Development dependencies (pytest, mypy, ruff)
└── README.md                     # General setup & quickstart documentation
```

---

## 🎮 Feature & Game Modules

| Module | Slash Commands | Description |
|---|---|---|
| **Tic-Tac-Toe** | `/tic-tac-toe` | 1v1 challenge with 3x3, 4x4, or 5x5 grid sizes. Includes interactive Discord UI buttons. |
| **Wordle** | `/wordle_play`, `/wordle_guess` | Guess hidden 5-letter words within 6 tries. | `cogs.py`, `logic.py`, `repository.py` |
| **Trivia** | `/trivia` | Interactive 4-option trivia game powered by Open Trivia DB. Filters by category & difficulty. | 
| **Utils** | `/info`, `/announcement` | Bot system statistics (ping, uptime, changelog display) and message formatting. |

---

## 🗄️ Database & Schema

### Base Model (`Match`)
Defined in `src/shared/models.py`:
- **`match` table**:
  - `match_id` (BigInteger, Primary Key)
  - `player_id` (BigInteger, Discord User ID)
  - `start_time` (DateTime UTC)
  - `end_time` (DateTime UTC, optional)
  - `status` (`EMatchStatus` Enum: `PENDING`, `WIN`, `LOSS`, `TIMEOUT`, `DRAW`)

### Module Models
- **Tic-Tac-Toe**: Extends match data for two-player grid records.
- **Trivia**: Stores category, difficulty, question text, and correct answer associated with match logs.

### Database Migrations (Alembic)
- Migration scripts live in `migrations/versions/`.
- Generated autogenerate scripts map module models into PostgreSQL schema changes.

---

## ⚙️ Development Environment & Tooling

### Prerequisites & Execution
- **Python**: 3.11+ (virtual environment recommended at `.venv/`)
- **Docker Compose**:
  - `development` profile starts `postgres`, `socat` (port forwarding), and `adminer` (web interface at `http://localhost:8080`).
  - `production` profile builds and starts the full `bot` container.

### Developer Commands
```bash
# Execute unit & integration tests
.venv/bin/python -m pytest

# Static type checking
.venv/bin/mypy . --strict

# Code linting & formatting checks
.venv/bin/ruff check .

# Database Migrations
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head

# Run bot locally
.venv/bin/python src/main.py
```

---

## 💡 Guidelines for Adding New Features / Modules

When building new features or mini-games for StrachyBot, follow these conventions:

1. **Module Structure**: Create a new folder under `src/modules/<module_name>/`.
   - `cogs.py`: Inherit from `commands.Cog` and implement commands using `@app_commands.command`.
   - `models.py` (optional): Inherit from `shared.database.Base` or establish relations to `Match`.
   - `repository.py` (optional): Encapsulate database query functions.
   - `ui.py` (optional): Implement `discord.ui.View` or `discord.ui.Button` components.
2. **Database Access**: Always use `helpers.execute_db_operation(target=self.bot, db_func=your_func, ...)` to perform operations against the async database session factory.
3. **Error Handling**: Wrap command logic in `try...except` blocks and call `messages.handle_error()` on failures.
4. **UI View Message References**: When creating dynamic Discord views with timeouts, save the initial message reference (`view.message = await interaction.original_response()`) so the view's `on_timeout` method can update the UI.
5. **Testing**: Add corresponding test suites under `tests/modules/<module_name>/`. Ensure all tests pass with `.venv/bin/python -m pytest`.
