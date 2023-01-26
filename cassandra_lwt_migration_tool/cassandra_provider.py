import contextlib
from typing import Iterator, List, Set, Tuple

import cassandra.auth
import cassandra.cluster
import cassandra.metadata
import cassandra.policies
import cassandra.query

from .options import options


@contextlib.contextmanager
def cassandra_cluster_for_node(
    node_ip: str,
) -> Iterator[cassandra.cluster.Cluster]:
    """
    Context manager for a cassandra cluster instance with a whitelist policy that ensures
    that it only connects to the specified node.

    :param node_ip: The node to connect to.
    """

    auth = cassandra.auth.PlainTextAuthProvider(
        username=options.cassandra_username, password=options.cassandra_password
    )

    execution_profile = cassandra.cluster.ExecutionProfile(
        load_balancing_policy=cassandra.policies.WhiteListRoundRobinPolicy(hosts=[node_ip]),
        consistency_level=cassandra.cluster.ConsistencyLevel.ONE,
        serial_consistency_level=cassandra.cluster.ConsistencyLevel.LOCAL_SERIAL,
        retry_policy=cassandra.policies.NeverRetryPolicy,
        row_factory=cassandra.query.named_tuple_factory,
    )

    profiles = {node_ip: execution_profile}

    cluster = cassandra.cluster.Cluster(
        execution_profiles=profiles, contact_points=[node_ip], auth_provider=auth
    )

    cluster.protocol_version = cassandra.ProtocolVersion.V4

    yield cluster


@contextlib.contextmanager
def cassandra_session_for_node(node_ip: str) -> Iterator[cassandra.cluster.Session]:
    """
    Context manager for a cassandra session with a whitelist policy that ensures
    that it only connects to the specified node.

    :param node_ip: The node to connect to.
    """

    with cassandra_cluster_for_node(node_ip) as cluster:
        session = cluster.connect()
        yield session
