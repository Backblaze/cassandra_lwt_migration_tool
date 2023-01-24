import logging


class CassandraFetchPolicy:
    """
    Auto-adjusting fetch policy that will grab more rows on success and fewer on failure.
    """

    INITIAL_SIZE = 100
    MAX_SIZE = 5000
    MIN_SIZE = 2

    def __init__(self, initial_size=INITIAL_SIZE):
        self.fetch_size: int = initial_size

    def on_success(self, rows_fetched: int) -> None:
        """
        Should be called when a query succeeds. Increases fetch size by 10%.

        :param rows_fetched: # of rows successfully fetched.
        """

        logging.debug("Fetched %s rows", rows_fetched)
        if self.fetch_size <= rows_fetched:
            self.fetch_size = min(
                self.MAX_SIZE,
                max(self.fetch_size + 1, int((self.fetch_size * 11) / 10)),
            )

    def on_failure(self):
        """
        Should be called if a query fails. Decreases fetch size by 50%.
        """

        logging.debug("Failed to fetch %s rows", self.fetch_size)
        self.fetch_size = max(self.MIN_SIZE, int(self.fetch_size / 2))
