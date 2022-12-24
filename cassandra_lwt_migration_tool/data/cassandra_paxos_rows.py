import dataclasses
from datetime import datetime
from typing import Dict

from .cassandra_paxos_row import CassandraPaxosRow


@dataclasses.dataclass
class CassandraPaxosRows:
    asOf: datetime
    rows: Dict[str, CassandraPaxosRow]
