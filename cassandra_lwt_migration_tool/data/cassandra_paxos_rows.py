from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import Any, Dict

from .cassandra_paxos_row import CassandraPaxosRow


@dataclasses.dataclass
class CassandraPaxosRows:
    """
    Represents a mapping from a "key" that we derive to each row from a result set. Also includes a timestamp
    the rows were fetched at.
    """

    as_of: datetime
    rows: Dict[str, CassandraPaxosRow]

    def to_json(self) -> Dict[str, Any]:
        """Converts this class to a serializable representation."""

        return {
            "as_of": self.as_of.isoformat(),
            "rows": {key: row.to_json() for (key, row) in self.rows.items()},
        }

    @classmethod
    def from_json(cls, obj) -> CassandraPaxosRows:
        """Converts this class from a serializable representation"""

        return cls(
            as_of=datetime.fromisoformat(obj["as_of"]),
            rows=dict(
                map(
                    lambda entry: (entry[0], CassandraPaxosRow.from_json(entry[1])),
                    obj["rows"].items(),
                )
            ),
        )
