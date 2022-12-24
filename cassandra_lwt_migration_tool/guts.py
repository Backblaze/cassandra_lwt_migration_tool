from collections import namedtuple
from typing import Callable, Dict, Tuple, Any
from logging import getLogger

import cassandra.cluster
import cassandra.metadata

from .data.cassandra_paxos_row import CassandraPaxosRow
from .cassandra_fetch_policy import CassandraFetchPolicy
from .cassandra_provider import token_ranges

logger = getLogger(__name__)

NUM_RETRIES = 3

def check_completion(
        force_baseline_file_usage: bool,
        cassandra_session: cassandra.cluster.Session) -> int:
    pass


def visit_token_range(cassandra_session, token_range: Tuple[cassandra.metadata.Token, cassandra.metadata.Token],
                      full_query: str, pickup_query: str, visitor: Callable[[namedtuple], Any],
                      fetch_policy: CassandraFetchPolicy = CassandraFetchPolicy()) -> None:
    last_row_key = None

    for retry in range(NUM_RETRIES):
        try:
            if last_row_key is None:
                stmt = cassandra_session.prepare(full_query).bind(token_range)
            else:
                stmt = cassandra_session.prepare(pickup_query).bind((last_row_key, token_range[1]))

            stmt.fetch_size = fetch_policy.fetch_size

            logger.info('Executing statement [%s]', stmt)
            result_set: cassandra.cluster.ResultSet = cassandra_session.execute(stmt)

            rows_visited = 0
            for row in result_set:
                visitor(row)
                last_row_key = row.row_key
                rows_visited += 1

            fetch_policy.on_success(rows_visited)
            break
        except cassandra.DriverException:
            fetch_policy.on_failure()
            logger.warning('Error fetching the next set of rows... last_row: %s token_range: %s', last_row_key,
                           token_range, exc_info=True)
            continue


def retrieve_all_lwts(cassandra_session: cassandra.cluster.Session) -> Dict[str, CassandraPaxosRow]:
    paxos_rows: Dict[str, CassandraPaxosRow] = {}

    def visit_row(row: namedtuple):
        # We only care about rows with a non-null value in this field.
        if row.proposal_ballot is not None:
            paxos_row: CassandraPaxosRow = CassandraPaxosRow.from_cassandra_row(row)
            key: str = f'{paxos_row.row_key}:{paxos_row.cf_id}'
            paxos_rows[key] = paxos_row

    column_names = [
        'row_key', 'cf_id', 'in_progress_ballot', 'most_recent_commit',
        'most_recent_commit_at', 'most_recent_commit_version', 'proposal', 'proposal_ballot', 'proposal_version',
        'TOKEN(row_key)'
    ]

    full_range_query = f'SELECT {", ".join(column_names)} FROM system.paxos ' \
        + 'WHERE TOKEN(row_key) > ? AND TOKEN(row_key) <= ?;'

    pickup_range_query = f'SELECT {", ".join(column_names)} FROM system.paxos ' \
        + 'WHERE TOKEN(row_key) >= TOKEN(?) AND TOKEN(row_key) <= ?;'

    for token_range in token_ranges():
        visit_token_range(
            cassandra_session=cassandra_session,
            token_range=token_range,
            full_query=full_range_query,
            pickup_query=pickup_range_query,
            visitor=visit_row,
        )

    return paxos_rows

