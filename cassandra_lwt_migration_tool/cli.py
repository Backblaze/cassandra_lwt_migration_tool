import logging
import sys

from .cassandra_on_one_node import CassandraOnOneNode
from .constants import *
from .node_ip_file import read_cass_node_ip_file
from .options import options


def main():
    options.populate()

    from imp import reload

    reload(logging)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(process)d] %(filename)s:%(lineno)d (%(levelname)s) %(message)s",
        stream=sys.stdout,
    )

    logging.info("Initialized.")

    node_ips = read_cass_node_ip_file(options.node_ips_file_path)

    if options.mode == CHECK_TARGETING_NODES:
        pass  # Nothing to do here.
    elif options.mode == CAPTURE_BASELINE:
        initialize_baseline_dir()
    elif options.mode in (CHECK_COMPLETION, CHECK_BASELINE_COMPLETION):
        ensure_baseline_dir()
    else:
        raise ValueError(f"Unknown operation mode: {options.mode}")

    for node_name, node_ip in node_ips.items():
        # TODO: Make this a thread pool.
        on_one_node = CassandraOnOneNode(node_name, node_ip)
        on_one_node.call()


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
