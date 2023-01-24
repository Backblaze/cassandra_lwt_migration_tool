import dataclasses


@dataclasses.dataclass
class CassandraLwtFetchResult:
    node_name: str
    node_ip: str
    succeeded: bool = False
    operation_time_ms: int = 0
    outstanding_lwts: int = 0
