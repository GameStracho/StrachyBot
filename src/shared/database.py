import os

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_db_engine() -> AsyncEngine:
    """Creates asynchronous engine from the CONNECTION_STRING env variable."""
    # Format: postgresql+asyncpg://user:password@host:port/dbname
    connection_string: str = os.getenv(
        "CONNECTION_STRING", "postgresql+asyncpg://localhost:Password1234@localhost:5432/StrachyBot"
    )

    # 'echo=True' logs all generated SQL to the console (great for debugging, turn off in prod)
    return create_async_engine(connection_string, echo=False, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Creates factory for database sessions from an engine."""
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
