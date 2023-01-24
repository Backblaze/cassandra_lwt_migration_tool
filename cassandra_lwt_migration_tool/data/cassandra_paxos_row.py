from __future__ import annotations

import base64
import dataclasses
import uuid
from collections import namedtuple
from typing import Any, Dict, NamedTuple, Union, overload

from cassandra.query import dict_factory
from uuid import UUID

from .cassandra_parsed_proposal import CassandraParsedProposal
from ..data_utils import maybe_bytes, maybe_uuid

CassandraPaxosRowNamedTuple = NamedTuple(
    "Row",
    [
        ("row_key", bytes),
        ("cf_id", UUID),
        ("in_progress_ballot", UUID),
        ("most_recent_commit", bytes),
        ("most_recent_commit_at", UUID),
        ("most_recent_commit_version", int),
        ("proposal", bytes),
        ("proposal_ballot", UUID),
        ("proposal_version", int),
        ("system_token_row_key", int),
    ],
)


@dataclasses.dataclass
class CassandraPaxosRow:
    """
    An instance of a PaxosRow from the system.paxos table.

    cassandra blobs become hex strings and uuids

    """

    row_key: bytes  # blob
    cf_id: UUID  # uuid
    in_progress_ballot: UUID  # timeuuid

    most_recent_commit: bytes  # blob
    most_recent_commit_at: UUID  # timeuuid
    most_recent_commit_version: int  # int
    parsed_proposal: CassandraParsedProposal  # string
    proposal_ballot: UUID  # timeuuid
    proposal_version: int

    @classmethod
    def from_cassandra_row(cls, row: CassandraPaxosRowNamedTuple) -> CassandraPaxosRow:
        return CassandraPaxosRow(
            row.row_key,
            row.cf_id,
            row.in_progress_ballot,
            row.most_recent_commit,
            row.most_recent_commit_at,
            row.most_recent_commit_version,
            CassandraParsedProposal(row.proposal),
            row.proposal_ballot,
            row.proposal_version,
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            "row_key": self.row_key,
            "cf_id": self.cf_id,
            "in_progress_ballot": self.in_progress_ballot,
            "most_recent_commit": self.most_recent_commit,
            "most_recent_commit_at": self.most_recent_commit_at,
            "most_recent_commit_version": self.most_recent_commit_version,
            "parsed_proposal": self.parsed_proposal.to_json(),
            "proposal_ballot": self.proposal_ballot,
            "proposal_version": self.proposal_version,
        }

    @classmethod
    def from_json(cls, obj: Dict[str, Any]) -> CassandraPaxosRow:
        return cls(
            row_key=maybe_bytes(obj["row_key"]),
            cf_id=maybe_uuid(obj["cf_id"]),
            in_progress_ballot=maybe_uuid(obj["in_progress_ballot"]),
            most_recent_commit=maybe_bytes(obj["most_recent_commit"]),
            most_recent_commit_at=maybe_uuid(obj["most_recent_commit_at"]),
            most_recent_commit_version=obj["most_recent_commit_version"],
            parsed_proposal=CassandraParsedProposal.from_json(obj["parsed_proposal"]),
            proposal_ballot=maybe_uuid(obj["proposal_ballot"]),
            proposal_version=obj["proposal_version"],
        )

    @property
    def map_key(self) -> str:
        """Key used for storage in local maps and such. Not stored in cassandra directly."""
        return f"{self.row_key.hex()}:{self.cf_id}"
