## [1.0.5] - 2026-07-12

### Added
- PostgresSQL database with tables for tracking `wordle` and `tic-tac-toe` games
- Database migrations automatically updated on bot startup
- Adminer service to view and manage database table records during development
- `production` and `development` Docker Compose profiles to separate development-only services

### Fixed
- Resolved issues with `tic-tac-toe` data types that led to buttons not being responsive


## [1.0.4] - 2026-07-03

### Added
- New embed icons for `/info` and `/announcement` commands
- Dedicated error handling icon assets
- This changelog file

### Changed
- Scaled down asset dimensions for `wordle` and `tic-tac-toe` icons for better Discord UI rendering

---

## [1.0.3] - 2026-07-02

### Added
- New `/info` slash command to display bot statistics in new `utils` module
- Global error handlers to catch and log failed interactions cleanly
- Added custom `wordle` and `tic-tac-toe` icons

### Changed
- Created custom `StrachyBot` logo
- Moved `console.py` to `/src/shared/`
- Further simplified `main.py` by creating a bot specific class
- Moved `/announcement` command to `utils` module

### Fixed
- Fixed unhandled exceptions and crashing edge cases in the `/announcement` command

---

## [1.0.2] - 2026-06-27

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

## [1.0.1] - 2026-06-17

### Added
- Docker support and list of required packages
- Git utility (.gitignore, [README.md](README.md), LICENSE)
- CI/CD pipeline running linters, type checks and unit tests

### Fixed
- Added type annotations and resolved type difference issues

---

## [1.0.0] - 2023-02-17

### Added
- New `wordle`, `tic-tac-toe` and `quote-guess` mini games
- New `/announcement` command for creating pretty announcements
- User stats tracking played games and achieved wins
- Backups of user stats on Google Drive
