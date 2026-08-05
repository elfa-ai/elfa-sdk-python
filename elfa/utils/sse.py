"""
Minimal Server-Sent Events parser for Auto notification streams.

``iter_sse`` / ``aiter_sse`` consume httpx line iterators and yield one
``SSEMessage`` per event frame (frames are separated by a blank line).
"""

from typing import AsyncIterator, Iterable, Iterator, List, NamedTuple, Optional


class SSEMessage(NamedTuple):
    event: str
    data: str
    id: Optional[str]


def _parse_frame(lines: List[str]) -> Optional[SSEMessage]:
    event: Optional[str] = None
    sid: Optional[str] = None
    data: List[str] = []

    for line in lines:
        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            event = line[6:].strip()
        elif line.startswith("id:"):
            sid = line[3:].strip()
        elif line.startswith("data:"):
            value = line[5:]
            data.append(value[1:] if value.startswith(" ") else value)

    if not data and event is None:
        return None
    return SSEMessage(event=event or "message", data="\n".join(data), id=sid)


def iter_sse(lines: Iterable[str]) -> Iterator[SSEMessage]:
    frame: List[str] = []
    for raw in lines:
        line = raw.rstrip("\r")
        if line == "":
            message = _parse_frame(frame)
            frame = []
            if message:
                yield message
        else:
            frame.append(line)
    if frame:
        message = _parse_frame(frame)
        if message:
            yield message


async def aiter_sse(lines: AsyncIterator[str]) -> AsyncIterator[SSEMessage]:
    frame: List[str] = []
    async for raw in lines:
        line = raw.rstrip("\r")
        if line == "":
            message = _parse_frame(frame)
            frame = []
            if message:
                yield message
        else:
            frame.append(line)
    if frame:
        message = _parse_frame(frame)
        if message:
            yield message
