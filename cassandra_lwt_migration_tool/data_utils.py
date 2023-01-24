from typing import Union, overload
from uuid import UUID


@overload
def maybe_uuid(inp: str) -> UUID: ...


@overload
def maybe_uuid(inp: None) -> None: ...


def maybe_uuid(inp: Union[str, None]) -> Union[UUID, None]:
    if inp is None:
        return None

    return UUID(inp)


@overload
def maybe_bytes(inp: str) -> bytes: ...


@overload
def maybe_bytes(inp: None) -> None: ...


def maybe_bytes(inp: Union[str, None]) -> Union[bytes, None]:
    if inp is None:
        return None

    return bytes.fromhex(inp)
