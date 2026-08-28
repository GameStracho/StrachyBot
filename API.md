## 1. Tech Stack Overview

| Layer | Recommended Technology | Primary Responsibilities |
| --- | --- | --- |
| Core Game Logic | **Pure Python** (`dataclasses`, zero external deps) | Game rules, win validation, board state transforms. Completely decoupled from HTTP/Discord. |
| Backend API | **Python** (FastAPI + SQLAlchemy Async) | REST endpoints, WebSocket room server, auth/tokens, database interactions, logging. |
| Database | **PostreSQL** | User profiles, linked Discord IDs, unified stats, game match histories, application logs. |
| Web Frontend | **Astro** (with React Islands) | UI pages, shared layouts/styles, WebSockets client, Discord OAuth2 login UI. |
| Discord Client | **Python** (`discord.py`) | Slash commands, interactive embed buttons, HTTP client calling the backend API. |
| Shared Lib | **Python Package** (`shared/`) | Async logging handler, DB engine initialization, shared data models/schemas. |

## 2. Project Directory Structure

Organized as a monorepo so that the shared Python library works natively across the API and Bot.

```
StrachyBot/
│
├── shared/                       # SHARED PYTHON PACKAGE
│   ├── __init__.py
│   ├── database.py               # Async SQLAlchemy engine & base model
│   └── logger.py                 # Non-blocking async queue logger -> DB
│
├── api/                          # FASTAPI SERVER
│   ├── main.py                   # App startup, router mounts, logger initialization
│   ├── dependencies.py           # Auth verification & DB session helpers
│   └── modules/                  # DOMAIN-DRIVEN MODULES
│       ├── __init__.py
│       ├── wordle/
│       │   ├── game.py           # Pure Python Wordle rules
mini-game
│       │   ├── models.py         # DB models for Wordle stats
│       │   └── router.py         # REST endpoints (e.g. POST /api/games/wordle/guess)
│       └── tictactoe/
│           ├── game.py           # Pure Python Tic-Tac-Toe rules
│           ├── icon.aseprite     # Raw icon for Wordle mini-game
│           ├── icon.png          # Exported icon for Wordle mini-game
│           ├── models.py         # DB models for Tic-Tac-Toe matches
│           └── router.py         # WebSocket server for real-time rooms
│
└── bot/                          # DISCORD.PY CLIENT
    ├── bot.py                    # Bot entry point & event loops
    └── modules/                     # Command modules (Wordle, Tic-Tac-Toe) that call backend_api via HTTP (httpx/aiohttp)
    ├── __init__.py
    ├── wordle/
    |   ├── __init__.py
    |   ├── icon.aseprite     # Raw icon
    │   ├── icon.png          # Exported icon
    │   ├── ui.py             # Views, Buttons, Modals
    |   └── cog.py            # Commands
    └── tictactoe/
        ├── __init__.py
        ├── icon.aseprite     # Raw icon
        ├── icon.png          # Exported icon
        ├── ui.py             # Views, Buttons, Modals
        └── cog.py            # Commands
```

## 3. Tasks Handled by the API

The API acts as the **single source of truth** and application brain.

- Authentication & Account Linking:
    - Exposes endpoints to exchange Discord OAuth2 codes for user session tokens.
    - Maps web account IDs to `discord_ids` in the database.

- Game Rules Execution:
    - Imports `game.py` modules to validate player moves (e.g., verifying a Wordle guess or checking if a Tic-Tac-Toe cell is valid).

- Real-time Multiplayer Orchestration (WebSockets):
    - Manages active web room connections (`ConnectionManager`).
    - Broadcasts live board state updates to connected clients.
    - Enforces per-turn AFK timers and handles graceful 30-second disconnect recovery tasks.

- Centralized System Logging:
    - Receives non-blocking logs from background queues and writes formatted logs directly to the PostgreSQL database.

## 4. Important information before building the API
- Database structure **must** be backwards compatible with migration `e230d678fc75`.
- Database in migration `e230d678fc75` stores user Discord ids as plain `int` (without any `discord_` prefix). This should be changed so that the API supports both non-Discord and Discord users.
- The **Astro Web Frontend** is part of a separate project and will be created later.
- Docker Compose must offer these 3 profiles that run the following services (`scripts/setup.sh` and `README.md` must be updated to reflect this change):
  - Development - postgres, socat, adminer
  - Bot - postgres, adminer, api (without exposed port), bot
  - API - postgres, adminer, api
  - Production - postgres, adminer, api, bot
