## [2.0.0] Harder, Better, Faster, Stronger - 2026-08-16

### Added
- To-do list ([TODO.md](TODO.md) )
- Enabled `strict` type checking in CI
- Enabled database interface (`adminer` service) in production
- Scripts `restore.sh` for restoring backups and `setup.sh` for setting up the environment
- Updates of database records on each game update
- Custom shared type `User`
- Logging of used valid commands

### Changed
- Renamed custom AI agent
- Updated formatter (`ruff`) configuration - check line length, spacing, import order, naming style, etc.
- Moved console log functions to a separate module `console`
- Restructured `shared` module and simplified `shared` imports
- Balanced `Tic-Tac-Toe` 4x4 and 5x5 boards
- Separated game logic of all mini-games from UI
- Renamed `utils` module to `info` and changed its color from `blue` to `teal`
- Unified code style of all mini-games
- Improved appearance of warning messages

### Removed
- Google Drive backups
- User statistics recorded into JSON files
- Files that are not used anymore
- Unused `/announcement` command
- Adminer auto-login

### Fixed
- Increased `Trivia` timeout to 60 seconds
- Enabled permanent database storage for `postgres` service
- Moved `alembic-postgresql-enum` from `requirements-dev` to `requirements`
- Prevented starting the `Tic-Tac-Toe` game against oneself
- Automated `Tic-Tac-Toe` auto-play moves
- Hiding of secret words in `Wordle` daily challenge
- Reduced API calls by caching `Trivia` questions

---

## [1.3.0] Wordle 2.0 - 2026-08-09

### Added
- Expanded the list of seasonal player emojis and colors
- Title and author of the `Trivia` mini-game
- Author of the `Tic-Tac-Toe` mini-game, indicating who is currently on turn
- Confirmable `Random guess` and `Give up` buttons to the `Wordle` mini-game
- Showcase of used letters and daily challenge mode to the `Wordle` mini-game
- New `surrender` match status
- Guesses and *is_daily* tag to the `wordle_match` database table
- 29 *unit* and 5 *integration* tests for `wordle` module

### Changed
- Complete rewrite and modernization of the `Wordle` mini-game with database records and timeout handling
- Combined `/wordle_play` and `/wordle_guess` commands to a single command `/wordle`
- Moved all used emojis to `shared/ui.py`
- Updated the `Wordle` mini-game icon to match the new style

### Fixed
- Centered the `Trivia` mini-game icon
- Bot session closure and database engine disposal on shutdown
- Detection of changes to enum values during database migration generation
- Excluded `migrations` directory from linting and type checking
- Added permissions to test-writing agent

---

## [1.2.0] Tic-Tac-Toe 2.0 - 2026-07-30

### Added
- Auto-play feature for `Tic-Tac-Toe` mini-game allowing players to play against Discord bots
- `tic_tac_toe_match` database table for recording `Tic-Tac-Toe` matches
- Shared types (`Position`, `Vector`, `EDirection`) for grid-based mini-games
- `FAIL` log level category in console logger
- Development requirements file (`requirements-dev.txt`) and `ruff` linter configuration in `pyproject.toml`
- Project Context & Developer Reference
- Custom AI agent for creating automated tests
- 21 *unit* and 3 *integration* tests for `tic_tac_toe` module

### Changed
- Complete rewrite and modernization of `Tic-Tac-Toe` mini-game with database records and timeout handling
- Renamed `/tic_tac_toe` command to `/tic-tac-toe`
- Moved `Trivia` module UI components into `src/modules/trivia/ui.py`
- Simplified execution of database operations via `helpers.execute_db_operation`
- Updated CI workflow to install packages from `requirements-dev.txt`

### Fixed
- Linter errors (unordered imports, obsolete types from `types` module, general `Exception` throwing) after a `ruff` update.

---

## [1.1.0] Trivia - 2026-07-19

### Added
- `Trivia` mini-game where a player must answer a question (fetched from the *Open Trivia Database* API with 25 *category* and 4 *difficulty* settings) by selecting the correct answer from 4 options
- `trivia_match` database table for recording `Trivia` matches
- Checks preventing updates of *status* from `pending` to `pending` in `Wordle` and `Tic-Tac-Toe` mini-games
- Helper functions for loading Discord attachments and fetching a public API into a custom class
- 16 *unit* and 2 *integration* tests for `trivia` module

### Changed
- Log detailed error tracebacks instead of simple error descriptions
- Capitalized match *status* values
- Restructured `tests` folder
- Command for running automated tests

### Fixed
- Stripped time zone indicator from dates stored into the database
- Added missing type annotations

### Removed
- `Quote Guess` mini-game, which was a more niche version of the `Trivia` mini-game

---

## [1.0.5] Database Utility - 2026-07-12

### Added
- PostgresSQL database with tables for tracking `Wordle` and `Tic-Tac-Toe` mini-games
- Database migrations automatically updated on bot startup
- Adminer service to view and manage database table records during development
- `production` and `development` Docker Compose profiles to separate development-only services
- Optional automatic database backups to a git repository
- Parsing of the latest version from `CHANGELOG.md` in the `/info` command 

### Changed
- Embed title of the `/info` command

### Fixed
- Resolved issues with `Tic-Tac-Toe` data types that led to buttons not being responsive

### Deprecated
- Google Drive backups
- User statistics recorded into JSON files

---

## [1.0.4] Custom Embed Icons - 2026-07-03

### Added
- New embed icons for `/info` and `/announcement` commands
- Dedicated error handling icon assets
- This changelog file

### Changed
- Scaled down asset dimensions for `Wordle` and `Tic-Tac-Toe` icons for better Discord UI rendering

---

## [1.0.3] Bot Statistics - 2026-07-02

### Added
- New `/info` slash command to display bot statistics in new `utils` module
- Global error handlers to catch and log failed interactions cleanly
- Added custom `Wordle` and `Tic-Tac-Toe` icons

### Changed
- Created custom `StrachyBot` logo
- Moved `console.py` to `/src/shared/`
- Further simplified `main.py` by creating a bot specific class
- Moved `/announcement` command to `utils` module

### Fixed
- Fixed unhandled exceptions and crashing edge cases in the `/announcement` command

---

## [1.0.2] Restructure - 2026-06-27

### Added
- Automatic loading of available modules with *cogs*

### Changed
- Moved modules from `/lib` for `/src/modules/[module]`
- Moved `main.py` to `/src/main.py`
- Simplified `main.py`
- Simplified console logs and added functions for more convenient logging of common message categories (info, error, warning, success, debug)

### Removed
- Copies of `stats.json`, `stats.py` and `user_data.json`

---

## [1.0.1] DevOps Utility - 2026-06-17

### Added
- Docker support and list of required packages
- Git utility (.gitignore, [README.md](README.md), LICENSE)
- CI/CD pipeline running linters, type checks, and unit tests

### Fixed
- Added type annotations and resolved type difference issues

---

## [1.0.0] Initial Release - 2023-02-17

### Added
- New `Wordle`, `Tic-Tac-Toe` and `Quote Guess` mini-games
- New `/announcement` command for creating pretty announcements
- User stats tracking played games and achieved wins
- Backups of user stats on Google Drive
