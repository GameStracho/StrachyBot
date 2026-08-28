from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import db_manager


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides an asynchronous database session."""
    if not db_manager.db_session_factory:
        db_manager.initialize()

    if not db_manager.db_session_factory:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is not initialized.",
        )

    async with db_manager.db_session_factory() as session:
        yield session


# Type alias for cleaner route signatures
DBSession = Annotated[AsyncSession, Depends(get_db)]


async def verify_auth_token(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """Dependency to verify authorization token from request headers."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header.",
        )

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization token format.",
        )

    return token
