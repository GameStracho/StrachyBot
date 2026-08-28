import importlib
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared import db_manager, logger


def load_module_routers(app: FastAPI) -> None:
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
    try:
        db_manager.initialize()
        logger.info("API database manager initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize database in API: {e}")

    yield

    logger.info("Shutting down API application...")
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
load_module_routers(app)
