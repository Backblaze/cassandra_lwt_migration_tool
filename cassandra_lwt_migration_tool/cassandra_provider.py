import contextlib
from typing import Generator, Iterator, List, Set, Tuple

import cassandra.cluster
import cassandra.metadata
import cassandra.policies
import cassandra.query
import cassandra.auth

from .options import options


@contextlib.contextmanager
def cassandra_cluster_for_node(
    node_ip: str,
) -> Generator[cassandra.cluster.Cluster, None, None]:
    auth = cassandra.auth.PlainTextAuthProvider(
        username=options.cassandra_username, password=options.cassandra_password
    )

    execution_profile = cassandra.cluster.ExecutionProfile(
        load_balancing_policy=cassandra.policies.WhiteListRoundRobinPolicy(
            hosts=[node_ip]
        ),
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
    with cassandra_cluster_for_node(node_ip) as cluster:
        session = cluster.connect()
        yield session


def token_ranges(
    cass_session: cassandra.cluster.Session,
) -> List[Tuple[cassandra.metadata.Token, cassandra.metadata.Token]]:
    token_map: cassandra.metadata.TokenMap = cass_session.cluster.metadata.token_map
    tok_ranges: Set[Tuple[cassandra.metadata.Token, cassandra.metadata.Token]] = set()

    if len(token_map.ring) <= 1:
        raise ValueError("Cannot build token ranges for ring with only one token.")
    else:
        for i in range(len(token_map.ring)):
            start = token_map.ring[i].value
            nxt_idx: int = (i + 1) % len(token_map.ring)
            fin = token_map.ring[nxt_idx].value

            if i == (len(token_map.ring) - 1):
                tok_ranges.add((start, cassandra.metadata.MAX_LONG))
                tok_ranges.add((cassandra.metadata.MIN_LONG, fin))
            else:
                tok_ranges.add((start, fin))

    return list(sorted(tok_ranges, key=lambda r: r[0]))
