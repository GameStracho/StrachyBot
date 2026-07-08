import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from sqlalchemy.orm import DeclarativeBase

from shared import console

# Format: postgresql+asyncpg://user:password@host:port/dbname
CONNECTION_STRING: str = os.getenv("CONNECTION_STRING", "postgresql+asyncpg://localhost:Password1234@localhost:5432/StrachyBot")

# Create the Asynchronous Engine
# 'echo=True' logs all generated SQL to the console (great for debugging, turn off in production)
engine: AsyncEngine = create_async_engine(CONNECTION_STRING, echo=False, pool_pre_ping=True)

# Create the Session Factory
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Base class for models to inherit from
class Base(DeclarativeBase):
    pass
