import asyncio
import os

from dotenv import load_dotenv

from shared import console
from shared.bot import StrachyBot


async def main() -> None:
    profile: str = os.getenv("COMPOSE_PROFILES", "development")

    if profile == "development":
        load_dotenv()
        console.log_debug("Environment variables loaded.")

    token: str | None = os.getenv("DISCORD_TOKEN")

    if token is None:
        console.log_error("Could not load discord token.")
        return

    bot = StrachyBot()
    bot.create_db_session_factory()
    await bot.start(token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.log_info("Shutdown requested. Closing bot...")
