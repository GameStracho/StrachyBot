# 🤖 Discord Bot

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg?style=flat-for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Discord.py](https://img.shields.io/badge/discord.py-v2.3+-5865F2.svg?style=flat-for-the-badge&logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat-for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)
[![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%205-A22846.svg?style=flat-for-the-badge&logo=raspberrypi&logoColor=white)](https://www.raspberrypi.com)

## 📌 About
Discord bot with fun mini-games like *Wordle* and *Tic-Tac-Toe* built with **Python** and **[discord.py](https://discordpy.readthedocs.io/en/stable/)**. 

---

## 🛠️ Installation & Setup

### Option 1: Local Development
**Prerequisites**
 - Install [Python](https://www.python.org/downloads/)

1. Clone the repository and navigate into it:
   ```bash
   git clone https://github.com/GameStracho/StrachyBot
   cd StrachyBot
   ```
2. Copy `.env.example` configuration file and insert your token.
   ```bash
   cp .env.example .env
   sed -i 's/^DISCORD_TOKEN=.*/DISCORD_TOKEN=your-token-here/' .env
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
    ```
5. (Optional) *VS Code Configuration:* Ensure your python interpreter is set to the virtual environment. Press `Ctrl+Shift+P` (or `Cmd+Shift+P`), search for **Python: Select Interpreter**, and choose the one inside `./venv/bin/python`.
6. Run the bot locally
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
2. Copy `.env.example` configuration file and insert your token.
   ```bash
   cp .env.example .env
   sed -i 's/^DISCORD_TOKEN=.*/DISCORD_TOKEN=your-token-here/' .env
   ```
3. Build and start the container
   ```bash
    docker compose up --build

    # or start in detached process (in background)
    docker compose up --build -d
   ```

---
## 🔑 License
This project is licensed under the **GNU General Public License** - see the [LICENSE](LICENSE) file for details.