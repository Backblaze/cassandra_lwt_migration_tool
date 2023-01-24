from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import Any, Dict

from .cassandra_paxos_row import CassandraPaxosRow


@dataclasses.dataclass
class CassandraPaxosRows:
    as_of: datetime
    rows: Dict[str, CassandraPaxosRow]

    def to_json(self) -> Dict[str, Any]:
        return {
            "as_of": self.as_of.isoformat(),
            "rows": {key: row.to_json() for (key, row) in self.rows.items()},
        }

    @classmethod
    def from_json(cls, obj) -> CassandraPaxosRows:
        return cls(
            as_of=datetime.fromisoformat(obj["as_of"]),
            rows=dict(
                map(
                    lambda entry: (entry[0], CassandraPaxosRow.from_json(entry[1])),
                    obj["rows"].items(),
                )
            ),
        )
