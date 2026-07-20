from __future__ import annotations

from typing import Any, Iterator, Mapping, Protocol

from .models import AthenaChunk


class ChunkReader(Protocol):
    def read_chunks(
        self,
        sql: str,
        *,
        params: Mapping[str, Any] | list[str] | None = None,
    ) -> Iterator[AthenaChunk]: ...


class ChunkProcessor(Protocol):
    """Strategy aplicada igualmente a cada chunk."""

    def process(self, chunk: AthenaChunk) -> None: ...

