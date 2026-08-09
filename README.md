# 🤖 Discord Bot

[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg?style=flat-for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Discord.py](https://img.shields.io/badge/discord.py-v2.3.2-5865F2.svg?style=flat-for-the-badge&logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![Docker](https://img.shields.io/badge/docker-compose-%230db7ed.svg?style=flat-for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-316192.svg?style=flat-for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Adminer](https://img.shields.io/badge/Adminer-dockette%2Fadminer-2563eb.svg?style=flat-for-the-badge&logo=adminer&logoColor=white)](https://hub.docker.com/r/dockette/adminer)
[![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%205-A22846.svg?style=flat-for-the-badge&logo=raspberrypi&logoColor=white)](https://www.raspberrypi.com)

## 📌 About
Discord bot with fun mini-games like *Wordle* and *Tic-Tac-Toe* built with **Python** and **[discord.py](https://discordpy.readthedocs.io/en/stable/)**. 

---

## 🛠️ Installation & Setup

### Option 1: Local Development
**Prerequisites**
 - Install [Python](https://www.python.org/downloads/)
 - Install [Docker](https://docs.docker.com/engine/install/)
 - Install [Docker Compose](https://docs.docker.com/compose/install/)

1. Clone the repository and navigate into it:
   ```bash
   git clone https://github.com/GameStracho/StrachyBot
   cd StrachyBot
   ```
2. Copy `.env.example` configuration file and update the configuration.
   ```bash
   cp .env.example .env
   
   # insert your bot's token
   sed -i 's/^DISCORD_TOKEN=.*/DISCORD_TOKEN=your-token-here/' .env

   # set up database password (recommended)
   sed -i 's/^DATABASE_PASSWORD=.*/DATABASE_PASSWORD=your_new_password/' .env
   # or use a random password
   sed -i "s/^DATABASE_PASSWORD=.*/DATABASE_PASSWORD=$(openssl rand -base64 32 | tr -d '=+/')/" .env

   # change docker profile to development
   sed -i 's/^COMPOSE_PROFILES=.*/COMPOSE_PROFILES=development/' .env

   # (Optional) change adminer port if port 8080 is occupied
    sed -i 's/^ADMINER_PORT=.*/ADMINER_PORT=8080/' .env
   ```
3. Create and activate a local virtual environment:
    ```bash
    # On Linux/macOS
    python3 -m venv .venv
    source .venv/bin/activate

    # On Windows (Command Prompt)
    python -m venv .venv
    .venv\Scripts\activate.bat
    ```
4. Install the required modules locally:
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    ```
5. (Optional) *VS Code Configuration:* Ensure your python interpreter is set to the virtual environment. Press `Ctrl+Shift+P` (or `Cmd+Shift+P`), search for **Python: Select Interpreter**, and choose the one inside `./venv/bin/python`.
6. Run docker services (database and adminer)
   ```bash
    docker compose up --build

    # or start in detached (background) process
    docker compose up --build -d
    ```
7. Update database to latest migration
   ```bash
   alembic upgrade head
   ```
8. Run the bot locally
    ```bash
    # Linux/macOS
    python3 src/main.py

    # Windows
    python src/main.py
    ```

### Option 2: Docker hosting
**Prerequisites**
 - Install [Docker](https://docs.docker.com/engine/install/)
 - Install [Docker Compose](https://docs.docker.com/compose/install/)

1. Clone the repository and navigate into it:
   ```bash
   git clone https://github.com/GameStracho/StrachyBot
   cd StrachyBot
   ```
2. Copy `.env.example` configuration file and update the configuration.
   ```bash
   cp .env.example .env
   
   # insert your bot's token
   sed -i 's/^DISCORD_TOKEN=.*/DISCORD_TOKEN=your-token-here/' .env

   # set up database password
   sed -i 's/^DATABASE_PASSWORD=.*/DATABASE_PASSWORD=your_new_password/' .env
   # or use a random password instead (recommended)
   sed -i "s/^DATABASE_PASSWORD=.*/DATABASE_PASSWORD=$(openssl rand -base64 32 | tr -d '=+/')/" .env
   ```
3. Build and start the StrachyBot container and database service
   ```bash
    docker compose up --build

    # or start in detached (background) process
    docker compose up --build -d
   ```

### Automatic database backups (optional)
1. Create a new **private** StrachyBotBackups repository on [GitHub](https://github.com/new)
2. Add SSH key to your [GitHub account](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account)
3. Clone the StrachyBotBackups repository into `backups`
   ```bash
      git clone git@github.com:YOUR-GITHUB-USERNAME/StrachyBotBackups.git backups
   ```
4. Update backup script's privileges to make it executable
   ```bash
   chmod +x scripts/backup.sh
   ```
5. Open cron manager terminal.
   ```bash
   crontab -e
   ```
6. Add new cron job to the **bottom of the file**. This job executes the backup script every dat at 2 am and logs errors into `backups/err.log`.
   ```bash
   0 2 * * * /bin/bash /absolute-path-to-StrachyBot/scripts/backup.sh 2> /absolute-path-to-StrachyBot/backups/err.log
   ```
---

## ⚙️ Developer Commands

- `ruff check .` - run static syntax check
- `mypy .` - run static type validation
- `alembic revision --autogenerate -m "MIGRATION NAME"` - create database migration
- `alembic upgrade head` - apply migrations
- `alembic downgrade -1` - revert last migration
- `python3 -m pytest` - run unit tests

---

## 🔑 License
This project is licensed under the **GNU General Public License** - see the [LICENSE](LICENSE) file for details.

---
## 🔁 Changelog

To see a full list of changes between releases, please refer to [CHANGELOG](CHANGELOG.md) file.
