from __future__ import annotations

import dataclasses
from collections import namedtuple
from cassandra.query import dict_factory
from uuid import UUID

from .cassandra_parsed_proposal import CassandraParsedProposal


@dataclasses.dataclass
class CassandraPaxosRow:
    """
    An instance of a PaxosRow from the system.paxos table.

    cassandra blobs become hex strings and uuids

    """
    row_key: str  # blob
    cf_id: UUID    # uuid
    in_progress_ballot: UUID  # timeuuid

    most_recent_commit: str  # blob
    most_recent_commit_at: UUID  # timeuuid
    most_recent_commit_version: int  # int
    parsed_proposal: CassandraParsedProposal  # string
    proposal_ballot: UUID  # timeuuid
    proposal_version: int

    @classmethod
    def from_cassandra_row(cls, row: namedtuple) -> CassandraPaxosRow:
        return CassandraPaxosRow(
            row.row_key,
            row.cf_id,
            row.in_progress_ballot,
            row.most_recent_commit,
            row.most_recent_commit_at,
            row.most_recent_commit_version,
            CassandraParsedProposal(row.proposal),
            row.proposal_ballot,
            row.proposal_version
        )

