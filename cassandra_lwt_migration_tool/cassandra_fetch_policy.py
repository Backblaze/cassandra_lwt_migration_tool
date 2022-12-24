class CassandraFetchPolicy:
    INITIAL_SIZE = 100
    MAX_SIZE = 5000
    MIN_SIZE = 2

    def __init__(self, initial_size = INITIAL_SIZE):
        self.fetch_size: int = initial_size

    def on_success(self, rows_fetched: int) -> None:
        if self.fetch_size <= rows_fetched:
            self.fetch_size = min(self.MAX_SIZE,
                                  max(self.fetch_size + 1,
                                      int((self.fetch_size * 11) / 10)))

    def on_failure(self):
        self.fetch_size = max(self.MIN_SIZE, int(self.fetch_size / 2))
