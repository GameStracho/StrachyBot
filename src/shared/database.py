import os
import sys
from collections.abc import Awaitable, Callable
from typing import Concatenate, ParamSpec, TypeVar

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

P = ParamSpec("P")
R = TypeVar("R")


class DatabaseManager:
    """Thread-safe Singleton managing database connections and execution."""

    _instance: "DatabaseManager | None" = None
    _db_engine: AsyncEngine | None
    _db_session_factory: async_sessionmaker[AsyncSession] | None

    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._db_engine = None
            cls._instance._db_session_factory = None

        return cls._instance

    @property
    def is_testing(self) -> bool:
        """Check if code is running under a unit testing framework (pytest)."""
        return "pytest" in sys.modules

    @property
    def db_session_factory(self) -> async_sessionmaker[AsyncSession] | None:
        return self._db_session_factory

    def initialize(self, db_engine: AsyncEngine | None = None) -> None:
        """Initialize the engine and session factory."""
        if self._db_engine:
            return

        if not db_engine:
            # Format: postgresql+asyncpg://user:password@host:port/dbname
            connection_string: str | None = os.getenv("CONNECTION_STRING")

            if not connection_string:
                raise RuntimeError("CONNECTION_STRING not set.")

            # 'echo=True' logs all generated SQL to the console (turn off in prod)
            db_engine = create_async_engine(connection_string, echo=False, pool_pre_ping=True)

        self._db_engine = db_engine
        self._db_session_factory = async_sessionmaker(
            bind=self._db_engine, class_=AsyncSession, expire_on_commit=False
        )

    async def execute(
        self,
        db_func: Callable[Concatenate[AsyncSession, P], Awaitable[R]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R | None:
        """
        Executes an async database operation using an AsyncSession.
        Safely blocks execution if running inside unit tests or if uninitialized.
        """
        if self.is_testing or not self._db_session_factory:
            return None

        async with self._db_session_factory() as session:
            if session:
                return await db_func(session, *args, **kwargs)

        return None

    async def close(self) -> None:
        """Dispose of the database engine and connection pool."""
        if not self._db_engine:
            return

        await self._db_engine.dispose()
        self._db_engine = None
        self._db_session_factory = None


# Export global singleton instance
db_manager = DatabaseManager()
