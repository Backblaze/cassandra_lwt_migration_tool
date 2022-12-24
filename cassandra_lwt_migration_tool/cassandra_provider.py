import contextlib
import functools
from typing import Generator, Set, Tuple

import cassandra.cluster
import cassandra.metadata
import cassandra.policies
import cassandra.query
import cassandra.auth

from .options import options

@contextlib.contextmanager
def cassandra_cluster() -> Generator[cassandra.cluster.Cluster, None, None]:
    auth = cassandra.auth.PlainTextAuthProvider(
        username=options.username,
        password=options.password
    )

    execution_profile = cassandra.cluster.ExecutionProfile(
        load_balancing_policy=cassandra.policies.WhiteListRoundRobinPolicy(hosts=['cass-910-0001']),
        consistency_level=cassandra.cluster.ConsistencyLevel.ONE,
        serial_consistency_level=cassandra.cluster.ConsistencyLevel.LOCAL_SERIAL,
        retry_policy=cassandra.policies.NeverRetryPolicy,
        row_factory=cassandra.query.named_tuple_factory,
    )

    profiles = {'cass-910-0000': execution_profile}

    cluster = cassandra.cluster.Cluster(
        execution_profiles=profiles,
        contact_points=['cass-910-0001'],
        auth_provider=auth
    )

    yield cluster


@contextlib.contextmanager
def cassandra_session() -> Generator[cassandra.cluster.Session, None, None]:
    with cassandra_cluster() as cluster:
        session = cluster.connect()
        yield session


# TODO: Is this ok to cache?
@functools.lru_cache
def token_ranges() -> Set[Tuple[cassandra.metadata.Token, cassandra.metadata.Token]]:
    with cassandra_session() as session:
        token_map: cassandra.metadata.TokenMap = session.cluster.metadata.token_map
        tok_ranges: Set[Tuple[cassandra.metadata.Token, cassandra.metadata.Token]] = set()

        if len(token_map.ring) <= 1:
            raise ValueError('Cannot build token ranges for ring with only one token.')
        else:
            for i in range(len(token_map.ring)):
                nxt: int = (i + 1) % len(token_map.ring)
                tok_ranges.add((token_map.ring[i].value, token_map.ring[nxt].value))

        return tok_ranges





