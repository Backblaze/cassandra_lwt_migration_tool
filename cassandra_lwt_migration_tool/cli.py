import logging
import sys
from asyncio import Future
from concurrent.futures import Executor, ThreadPoolExecutor
from typing import List

from .cassandra_on_one_node import CassandraOnOneNode
from .constants import *
from .data.cassandra_lwt_fetch_result import CassandraLwtFetchResult
from .node_ip_file import read_cass_node_ip_file
from .options import options

LOG_FORMAT = "{asctime:s} [{process:06d}] {filename: >20.20}:{lineno:<6d} {levelname:>5.5} | {message:s}"


def main():
    options.populate()

    from imp import reload

    reload(logging)
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        style="{",
        stream=sys.stdout,
    )

    logging.warning("Initialized.")

    node_ips = read_cass_node_ip_file(options.node_ips_file_path)

    if options.mode == CHECK_TARGETING_NODES:
        pass  # Nothing to do here.
    elif options.mode == CAPTURE_BASELINE:
        initialize_baseline_dir()
    elif options.mode in (CHECK_COMPLETION, CHECK_BASELINE_COMPLETION):
        ensure_baseline_dir()
    else:
        raise ValueError(f"Unknown operation mode: {options.mode}")

    with ThreadPoolExecutor() as executor:
        futures = []
        for node_name, node_ip in node_ips.items():
            on_one_node = CassandraOnOneNode(node_name, node_ip)
            futures.append(executor.submit(on_one_node.call))

        verify_completion(futures)


def verify_completion(futures: List[Future]):
    """Tracks the completion of the executor."""

    found_error = False
    deltat_sum = 0
    outstanding_lwts = 0

    for future in futures:
        result: CassandraLwtFetchResult = future.result()  # Wait indefinitely

        if not result.succeeded:
            found_error = True

        deltat_sum += result.operation_time_ms
        outstanding_lwts += result.outstanding_lwts

        logging.info("%s: %d outstanding paxos entries", result.node_name, result.outstanding_lwts)

    logging.info("Any errors?: %s", found_error)
    logging.info("Average run time: %0.0fms", deltat_sum / len(futures))
    logging.info("Total outstanding LWTs: %d", outstanding_lwts)


def initialize_baseline_dir():
    """
    Attempts to create a new baseline directory
    """

    try:
        options.baseline_directory.mkdir(parents=True, exist_ok=False)
    except OSError:
        logging.error(f"Error creating baseline directory: {options.baseline_directory}")
        raise


def ensure_baseline_dir():
    """
    Ensures the expected baseline directory exists.
    """

    if not options.baseline_directory.exists():
        raise RuntimeError(
            f"When checking completion the baseline directory must already exist: {options.baseline_directory}"
        )
