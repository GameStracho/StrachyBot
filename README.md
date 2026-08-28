# 🤖 StrachyBot

[![](https://img.shields.io/badge/Invite_Bot-Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/oauth2/authorize?client_id=1024635572591001630&permissions=378880&integration_type=0&scope=bot+applications.commands)

## 📌 About
Modular Discord bot and backend service with fun mini-games like *Trivia*, *Wordle*, and *Tic-Tac-Toe* built with **Python 3.11+**, **[FastAPI](https://fastapi.tiangolo.com/)**, and **[discord.py](https://discordpy.readthedocs.io/en/stable/)**.

---

## 🏗️ Architecture Overview

StrachyBot is organized as a monorepo containing:
- **`shared/`**: Core shared library (database singleton engine, async logger to DB, models, and shared schemas).
- **`api/`**: FastAPI REST & WebSocket server acting as the application brain and single source of truth.
- **`bot/`**: Discord client handling slash commands and interactive views via the backend API.

---

## 🎮 Features & Commands

| Command | Description | Showcase |
|---|---|---|
| `/wordle` | Try to guess a 5-letter word in 6 tries. | ![Wordle Demo](docs/assets/wordle-demo.png) |
| `/tic-tac-toe` | Challenge someone in a 1v1 Tic-Tac-Toe match. | ![TTT Demo](docs/assets/tic-tac-toe-demo.png) |
| `/trivia` | Try to answer a quiz question by selecting 1 of 4 answers. | ![Trivia Demo](docs/assets/trivia-demo.png) |
| `/info` | Show important information about the bot. | ![Info Demo](docs/assets/info-demo.png) |

---

## 🛠️ Installation & Setup

### Option 1: Local Development
**Prerequisites**
 - Install [Python 3.11+](https://www.python.org/downloads/)
 - Install [Docker](https://docs.docker.com/engine/install/) & [Docker Compose](https://docs.docker.com/compose/install/)

1. Clone the repository and navigate into it:
   ```bash
   git clone https://github.com/GameStracho/StrachyBot
   cd StrachyBot
   ```
2. Make the setup script executable and run the script:
   > Select `1) Development` mode during setup.
   ```bash
   chmod u+x scripts/setup.sh
   ./scripts/setup.sh
   ```
3. Start database and adminer via Docker:
   ```bash
   docker compose up -d
   ```
   > Access Adminer at *[localhost:8080](http://localhost:8080/)*.
4. Run database migrations:
   ```bash
   alembic upgrade head
   ```
5. Run the API and Bot services locally:
   ```bash
   # Terminal 1: Run FastAPI backend
   uvicorn api.main:app --reload --port 8000

   # Terminal 2: Run Discord Bot client
   python bot/main.py
   ```

### Option 2: Docker Hosting (Production / Profiles)
StrachyBot supports dedicated Docker Compose profiles:
- **`development`**: Starts Postgres, Socat port forwarder, and Adminer.
- **`bot`**: Starts Postgres, Adminer, API (internal network only), and the Discord Bot.
- **`api`**: Starts Postgres, Adminer, and the API server with port exposed.
- **`production`**: Starts Postgres, Adminer, API (port exposed), and the Discord Bot.

To deploy via Docker:
```bash
./scripts/setup.sh  # Select your desired mode

# Build and start services
docker compose up --build -d
```

### Automatic database backups (optional)
1. Create a new **private** StrachyBotBackups repository on [GitHub](https://github.com/new)
2. Add SSH key to your [GitHub account](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account)
3. Clone the StrachyBotBackups repository into `backups`:
   ```bash
   git clone git@github.com:YOUR-GITHUB-USERNAME/StrachyBotBackups.git backups
   ```
4. Update backup script's privileges:
   ```bash
   chmod +x scripts/backup.sh
   ```
5. Open cron manager:
   ```bash
   crontab -e
   ```
6. Add new cron job:
   ```bash
   0 2 * * * /bin/bash /absolute-path-to-StrachyBot/scripts/backup.sh 2> /absolute-path-to-StrachyBot/backups/err.log
   ```

---

## ⚙️ Developer Commands

| Task | Command |
|---|---|
| Static syntax check | `ruff check .` | 
| Auto-format code | `ruff format .` |
| Static type check | `mypy . --strict` |
| Create database migration | `alembic revision --autogenerate -m "<NAME>"` |
| Apply migrations | `alembic upgrade head` |
| Revert last migration | `alembic downgrade -1` |
| Run unit tests | `python3 -m pytest` |

---

## 📄 Developer Reference

Information about the codebase is documented inside [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md).

---

## 🔑 License
This project is licensed under the **GNU General Public License** - see the [LICENSE](LICENSE) file for details.

## 🔁 Changelog
To see a full list of changes between releases, please refer to the [CHANGELOG.md](CHANGELOG.md) file.
