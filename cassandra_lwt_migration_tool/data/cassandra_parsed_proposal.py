import io
import uuid
import struct


class CassandraParsedProposal:
    """
    Represents a proposal parsed out of the raw bytes of a Paxos row.
    This does not completely parse the proposal, but we do need to read the IS_EMPTY flag.
    """

    IS_EMPTY_FIELD = 0x01

    uuid: str
    partition_key: bytes
    is_empty: bool
    flags: int
    raw_bytes: bytes

    def __init__(self, proposal: bytes):
        self.raw_bytes = proposal
        proposal_reader = io.BytesIO(initial_bytes=proposal)


        self.uuid = uuid.UUID(bytes=proposal_reader.read(16))
        partition_key_size: int = struct.unpack('B', proposal_reader.read(1))[0]
        self.partition_key = proposal_reader.read(partition_key_size)
        self.flags = struct.unpack('B', proposal_reader.read(1))[0]
        self.is_empty = ((self.flags & self.IS_EMPTY_FIELD) == 1)




