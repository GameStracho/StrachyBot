import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from sqlalchemy.orm import DeclarativeBase

def create_db_engine() -> AsyncEngine:
    """Creates asynchronous engine from the CONNECTION_STRING env variable."""    
    # Format: postgresql+asyncpg://user:password@host:port/dbname
    CONNECTION_STRING: str = os.getenv("CONNECTION_STRING", "postgresql+asyncpg://localhost:Password1234@localhost:5432/StrachyBot")

    # 'echo=True' logs all generated SQL to the console (great for debugging, turn off in production)
    return create_async_engine(CONNECTION_STRING, echo=False, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Creates factory for database sessions from an engine."""
    return async_sessionmaker(
        bind=engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )


# Base class for models to inherit from
class Base(DeclarativeBase):
    pass
