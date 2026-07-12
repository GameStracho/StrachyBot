class DummyConnection:
    async def run_sync(self, _func):
        return None


class DummyTransaction:
    async def __aenter__(self):
        return DummyConnection()

    async def __aexit__(self, exc_type, exc, tb):
        return False
