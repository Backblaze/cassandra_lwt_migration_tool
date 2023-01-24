import json
from typing import Any
from uuid import UUID


class ClmtJsonEncoder(json.JSONEncoder):
    """JSON encoder to make it simpler to serialize bytes and UUID objects."""

    def default(self, o: Any) -> Any:
        """Overridden default method."""

        if isinstance(o, bytes):
            return o.hex()
        if isinstance(o, UUID):
            return str(o)

        return json.JSONEncoder.default(self, o)
