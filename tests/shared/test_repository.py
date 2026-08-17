from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from shared.repository import delete_expired_logs


@pytest.mark.asyncio
async def test_delete_expired_logs_returns_rowcount() -> None:
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.rowcount = 5
    mock_session.execute.return_value = mock_result

    cutoff = datetime.now(UTC)
    deleted_count = await delete_expired_logs(mock_session, cutoff)

    assert deleted_count == 5
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()
