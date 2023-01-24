import json
import logging
import os

from collections import namedtuple
from datetime import datetime
from ipaddress import ip_address
from typing import Any, Callable, ContextManager, Dict, NamedTuple, Tuple

import cassandra
import cassandra.cluster
import cassandra.metadata

from .cassandra_fetch_policy import CassandraFetchPolicy
from .cassandra_provider import cassandra_session_for_node, token_ranges
from .constants import *
from .data.cassandra_lwt_fetch_result import CassandraLwtFetchResult
from .data.cassandra_paxos_row import CassandraPaxosRow, CassandraPaxosRowNamedTuple
from .data.cassandra_paxos_rows import CassandraPaxosRows
from .json_helper import ClmtJsonEncoder
from .options import options


class CassandraSingleNodeError(RuntimeError):
    pass


class CassandraOnOneNode:
    NUM_RETRIES = 3

    def __init__(self, node_name: str, node_ip: str):
        self.node_name = node_name
        self.node_ip = node_ip
        self.session_cm = cassandra_session_for_node(node_ip=node_ip)
        self.session = self.session_cm.__enter__()

    def __del__(self):
        try:
            self.session_cm.__exit__(None, None, None)
        except RuntimeError as e:
            self.node_print(msg=f"{e}")
            pass  # best effort.

    def call(self):
        result = CassandraLwtFetchResult(self.node_name, self.node_ip)
        start = datetime.utcnow()

        if options.mode == CAPTURE_BASELINE:
            result.outstanding_lwts = self.capture_one_baseline()
        elif options.mode == CHECK_COMPLETION:
            result.outstanding_lwts = self.check_completion(
                force_baseline_file_usage=False
            )
        elif options.mode == CHECK_BASELINE_COMPLETION:
            result.outstanding_lwts = self.check_completion(
                force_baseline_file_usage=True
            )
        elif options.mode == CHECK_TARGETING_NODES:
            pass  # This is fine, since we already connected to cass.
        else:
            raise ValueError(f"Unknown mode of operations: {options.mode}")

        result.succeeded = True
        result.operation_time_ms = int((datetime.utcnow() - start).seconds * 1000)

        return result

    def capture_one_baseline(self) -> int:
        self.node_print("Capturing baseline")
        paxos_rows = self.retrieve_all_lwts()

        path = os.path.join(options.baseline_directory, f"{self.node_name}.json")
        with open(path, "w") as fd:
            json.dump(paxos_rows.to_json(), fd, cls=ClmtJsonEncoder)

        return len(paxos_rows.rows)

    UPDATE_FILE_PREFIX = "update_"

    def check_completion(self, force_baseline_file_usage: bool) -> int:
        self.node_print(
            f"Checking completion with {options.baseline_directory} as user {options.cassandra_username}."
        )
        baseline_path = os.path.join(
            options.baseline_directory, f"{self.node_name}.json"
        )
        updated_baseline_path = os.path.join(
            options.baseline_directory,
            f"{self.UPDATE_FILE_PREFIX}{self.node_name}.json",
        )

        baseline_state = None

        path_to_read = (
            updated_baseline_path
            if os.path.exists(updated_baseline_path)
            else baseline_path
        )
        with open(path_to_read, "r") as fd:
            baseline_state = CassandraPaxosRows.from_json(json.load(fd))

        if baseline_state is None:
            raise RuntimeError(f"Could not load baseline from {baseline_path}")
        if len(baseline_state.rows) == 0:
            self.node_print("Baseline captures no LWTs, so nothing to do.")
            return 0

        captured_rows = self.retrieve_all_lwts()
        outstanding_rows: Dict[str, CassandraPaxosRow] = {}
        for map_key, row in baseline_state.rows.items():
            if (
                (matched_row := captured_rows.rows.get(map_key, None)) is not None
                and matched_row.in_progress_ballot == row.in_progress_ballot
            ):
                outstanding_rows[matched_row.map_key] = matched_row

        outstanding_state = CassandraPaxosRows(
            as_of=captured_rows.as_of, rows=outstanding_rows
        )

        with open(updated_baseline_path, "w") as fd:
            json.dump(outstanding_state.to_json(), fd, cls=ClmtJsonEncoder)

        self.node_print(f"{len(outstanding_state.rows)} rows still outstanding.")
        return len(outstanding_state.rows)

    def raise_if_not_connected_to_ip(self):
        """
        Raises an exception if cassandra is not connected to the host it is expceted to be.

        :param cassandra_session: Cassandra session.
        :param node_name: Cassandra node hostname
        :param node_ip: Cassandra node ip
        :raises CassandraSingleNodeError
        """

        prepared_stmt = self.session.prepare(
            "select key, data_center, listen_address from system.local"
        )
        bound_stmt = prepared_stmt.bind()

        result_set = self.session.execute(bound_stmt)
        row = result_set.one()

        if row is None:
            raise CassandraSingleNodeError("No system.local row.")

        listen_addr = row.listen_address

        self.node_print(msg=f"listen_address={listen_addr}")
        self.node_print(msg=f"data_center={row.data_center}")

        if ip_address(self.node_ip) != ip_address(listen_addr):
            raise CassandraSingleNodeError(
                f"Not connected to correct node [{self.node_ip}] != [{listen_addr}] "
            )

        if result_set.one() is not None:
            raise CassandraSingleNodeError(f"Unexpected second system.local row.")

    def retrieve_all_lwts(self) -> CassandraPaxosRows:
        """Fetches all open LWTs on this node from the system.paxos table."""

        start_time = datetime.utcnow()
        paxos_rows: Dict[str, CassandraPaxosRow] = {}

        def visit_row(row: CassandraPaxosRowNamedTuple):
            # We only care about rows with a non-null value in this field.
            if row.proposal_ballot is not None:
                paxos_row: CassandraPaxosRow = CassandraPaxosRow.from_cassandra_row(row)
                paxos_rows[paxos_row.map_key] = paxos_row

        column_names = [
            "row_key",
            "cf_id",
            "in_progress_ballot",
            "most_recent_commit",
            "most_recent_commit_at",
            "most_recent_commit_version",
            "proposal",
            "proposal_ballot",
            "proposal_version",
            "TOKEN(row_key)",
        ]

        full_range_query = (
            f'SELECT {", ".join(column_names)} FROM system.paxos '
            + "WHERE TOKEN(row_key) > ? AND TOKEN(row_key) <= ?;"
        )

        pickup_range_query = (
            f'SELECT {", ".join(column_names)} FROM system.paxos '
            + "WHERE TOKEN(row_key) >= TOKEN(?) AND TOKEN(row_key) <= ?;"
        )

        for token_range in token_ranges(self.session):
            self.visit_token_range(
                token_range=token_range,
                full_query=full_range_query,
                pickup_query=pickup_range_query,
                visitor=visit_row,
            )

        return CassandraPaxosRows(as_of=start_time, rows=paxos_rows)

    def visit_token_range(
        self,
        token_range: Tuple[cassandra.metadata.Token, cassandra.metadata.Token],
        full_query: str,
        pickup_query: str,
        visitor: Callable[[NamedTuple], Any],
        fetch_policy: CassandraFetchPolicy = CassandraFetchPolicy(),
    ) -> None:
        """
        Calls a callable on each row from the given token range. Configurable with regards
        to what happens when data cannot be fetched.

        :param token_range: The token bounds to visit.
        :param full_query: The query for the full dataset.
        :param pickup_query: The query that is used to resume partial dataset fetches.
        :param visitor: A callable that is run on each row.
        :param fetch_policy: Configure fetch behavior.
        :return:
        """

        last_row_key = None

        for retry in range(self.NUM_RETRIES):
            try:
                if last_row_key is None:
                    stmt = self.session.prepare(full_query).bind(token_range)
                else:
                    stmt = self.session.prepare(pickup_query).bind(
                        (last_row_key, token_range[1])
                    )

                stmt.fetch_size = fetch_policy.fetch_size

                self.node_print(f"Executing statement [{stmt}]")
                result_set: cassandra.cluster.ResultSet = self.session.execute(stmt)

                rows_visited = 0
                for row in result_set:
                    visitor(row)
                    last_row_key = row.row_key
                    rows_visited += 1

                fetch_policy.on_success(rows_visited)
                break
            except cassandra.DriverException:
                fetch_policy.on_failure()
                logging.warning(
                    "Error fetching the next set of rows... last_row: %s token_range: %s",
                    last_row_key,
                    token_range,
                    exc_info=True,
                )
                continue

    def node_print(self, msg: str) -> None:
        logging.info(f"\tNode {self.node_name} [{self.node_ip}]: {msg}")

    def node_print_exc(self, e: RuntimeError):
        logging.warning(f"{self.node_name} [{self.node_ip}]: {e}", stack_info=True)
