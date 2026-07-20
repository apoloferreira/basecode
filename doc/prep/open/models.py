from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

import pandas as pd


@dataclass(frozen=True, slots=True)
class AthenaChunk:
    index: int
    dataframe: pd.DataFrame
    query_execution_id: str | None
    query_metadata: Mapping[str, Any]

    @property
    def row_count(self) -> int:
        return len(self.dataframe.index)

    @property
    def idempotency_key(self) -> str:
        query_id = self.query_execution_id or "query-id-unavailable"
        return f"{query_id}:{self.index}"


@dataclass(frozen=True, slots=True)
class PipelineSummary:
    run_id: str
    chunks_processed: int
    rows_processed: int
    started_at: datetime
    finished_at: datetime

    @property
    def elapsed_seconds(self) -> float:
        return (self.finished_at - self.started_at).total_seconds()

