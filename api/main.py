import asyncio
import importlib
import os
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any

# Ensure the project root is on sys.path when running this file directly
# (e.g. `uvicorn api.main:app` from root), so that `shared`, `api`, etc. are importable.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared import db_manager, logger
from shared.repository import delete_expired_logs


async def _cleanup_old_logs() -> None:
    """Deletes database logs older than 7 days."""
    cutoff_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=7)
    deleted_rows: int | None = await db_manager.execute(
        db_func=delete_expired_logs, cutoff=cutoff_date
    )
    if deleted_rows:
        logger.info(f"Cleaned up {deleted_rows} logs older than 7 days.")


async def _cleanup_logs_periodic_task() -> None:
    """Runs database log cleanup once every 24 hours."""
    while True:
        try:
            await _cleanup_old_logs()
            await asyncio.sleep(24 * 3600)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error during periodic log cleanup: {e}")
            await asyncio.sleep(3600)


def _load_module_routers(app: FastAPI) -> None:
    """Dynamically loads and registers routers from the api/modules directory."""
    modules_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "modules"))
    if not os.path.exists(modules_dir):
        return

    for entry in os.listdir(modules_dir):
        module_path = os.path.join(modules_dir, entry)
        if not os.path.isdir(module_path) or entry.startswith("_"):
            continue

        router_file = os.path.join(module_path, "router.py")
        if os.path.exists(router_file):
            try:
                mod = importlib.import_module(f"api.modules.{entry}.router")
                router: APIRouter | None = getattr(mod, "router", None)
                if router and isinstance(router, APIRouter):
                    app.include_router(router)
                    logger.info(f"Mounted API router for domain module '{entry}'.")
            except Exception as e:
                logger.critical(f"Failed to mount API router for module '{entry}': {e}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle management: startup & shutdown."""
    logger.info("Initializing API application...")

    load_dotenv()
    logger.debug("Environment variables loaded.")

    try:
        db_manager.initialize()
        logger.info("API database manager initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize database in API: {e}")

    cleanup_task = asyncio.create_task(_cleanup_logs_periodic_task())

    yield

    logger.info("Shutting down API application...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

    await db_manager.close()
    logger.info("API database connections disposed.")


app = FastAPI(
    title="StrachyBot API",
    description="Backend API and WebSocket service for StrachyBot mini-games and stats.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for web frontend clients (e.g. Astro)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production domains when configured
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["Health"])
async def health_check() -> dict[str, Any]:
    """Health check endpoint for container orchestrators and monitoring."""
    return {"status": "ok", "service": "StrachyBot API", "version": "1.0.0"}


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Root welcome endpoint."""
    return {"message": "Welcome to StrachyBot API Server"}


# Mount all available domain module routers
_load_module_routers(app)
