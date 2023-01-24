from __future__ import annotations

import base64
import io
from uuid import UUID
import struct

from cassandra_lwt_migration_tool.data_utils import maybe_bytes


class CassandraParsedProposal:
    """
    Represents a proposal parsed out of the raw bytes of a Paxos row.
    This does not completely parse the proposal, but we do need to read the IS_EMPTY flag.
    """

    IS_EMPTY_FIELD = 0x01

    uuid: uuid.UUID
    partition_key: bytes
    is_empty: bool
    flags: int
    raw_bytes: bytes

    def __init__(self, proposal: bytes):
        self.raw_bytes = proposal
        proposal_reader = io.BytesIO(initial_bytes=proposal)

        self.uuid = UUID(bytes=proposal_reader.read(16))
        partition_key_size: int = struct.unpack("B", proposal_reader.read(1))[0]
        self.partition_key = proposal_reader.read(partition_key_size)
        self.flags = struct.unpack("B", proposal_reader.read(1))[0]
        self.is_empty = (self.flags & self.IS_EMPTY_FIELD) == 1

    def to_json(self):
        return {"raw_bytes": self.raw_bytes}

    @classmethod
    def from_json(cls, obj) -> CassandraParsedProposal:
        return cls(proposal=maybe_bytes(obj["raw_bytes"]))
