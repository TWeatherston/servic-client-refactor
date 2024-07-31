class InMemoryCache:
    """Basic in-memory cache implementation. This is a simple cache that stores key-value pairs in memory. Its use
    should be avoided where possible (e.g. in production) as it's not scalable and will not persist data across
    multiple instances of the application."""

    def __init__(self):
        self.cache = {}

    def get(self, key: str) -> str:
        return self.cache.get(key)

    def set(self, key: str, value: str, *args, **kwargs) -> None:
        self.cache[key] = value
