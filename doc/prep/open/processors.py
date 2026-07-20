from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from .models import AthenaChunk

Transform = Callable[[pd.DataFrame], pd.DataFrame]
Sink = Callable[[pd.DataFrame, str], None]


class TransformAndWriteProcessor:
    """Processor generico composto por duas Strategies injetadas."""

    def __init__(self, transform: Transform, sink: Sink) -> None:
        self._transform = transform
        self._sink = sink

    def process(self, chunk: AthenaChunk) -> None:
        transformed = self._transform(chunk.dataframe)
        # A chave permite que o destino implemente deduplicacao/idempotencia.
        self._sink(transformed, chunk.idempotency_key)

