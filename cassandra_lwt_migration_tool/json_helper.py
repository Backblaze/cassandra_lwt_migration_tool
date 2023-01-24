import base64
import json
from typing import Any
from uuid import UUID


class ClmtJsonEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, bytes):
            return o.hex()
        if isinstance(o, UUID):
            return str(o)

        return json.JSONEncoder.default(self, o)
