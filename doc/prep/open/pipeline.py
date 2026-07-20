from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .contracts import ChunkProcessor, ChunkReader
from .models import AthenaChunk, PipelineSummary


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_delay_seconds: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay_seconds: float = 30.0

    def __post_init__(self) -> None:
        if self.max_attempts <= 0:
            raise ValueError("max_attempts deve ser maior que zero")
        if self.initial_delay_seconds < 0:
            raise ValueError("initial_delay_seconds nao pode ser negativo")
        if self.backoff_multiplier < 1:
            raise ValueError("backoff_multiplier deve ser pelo menos 1")
        if self.max_delay_seconds < 0:
            raise ValueError("max_delay_seconds nao pode ser negativo")

    def delay_after_failure(self, attempt: int) -> float:
        delay = self.initial_delay_seconds * (self.backoff_multiplier ** (attempt - 1))
        return min(delay, self.max_delay_seconds)


class ChunkProcessingError(RuntimeError):
    def __init__(self, chunk: AthenaChunk, attempts: int) -> None:
        super().__init__(
            f"Falha definitiva no chunk {chunk.index} "
            f"({chunk.idempotency_key}) apos {attempts} tentativa(s)"
        )
        self.chunk = chunk
        self.attempts = attempts


class ChunkPipeline:
    """Application Service que coordena leitura, retry e processamento."""

    def __init__(
        self,
        reader: ChunkReader,
        processor: ChunkProcessor,
        *,
        retry_policy: RetryPolicy | None = None,
        sleep: Callable[[float], None] = time.sleep,
        logger: logging.Logger | None = None,
    ) -> None:
        self._reader = reader
        self._processor = processor
        self._retry_policy = retry_policy or RetryPolicy()
        self._sleep = sleep
        self._logger = logger or logging.getLogger(__name__)

    def run(
        self,
        sql: str,
        *,
        params: Mapping[str, Any] | list[str] | None = None,
        run_id: str | None = None,
    ) -> PipelineSummary:
        execution_id = run_id or str(uuid.uuid4())
        started_at = datetime.now(UTC)
        chunks_processed = 0
        rows_processed = 0

        self._logger.info("pipeline_start run_id=%s", execution_id)

        # O for cria backpressure: so busca o proximo DataFrame depois que o
        # processamento do atual termina.
        for chunk in self._reader.read_chunks(sql, params=params):
            if chunk.row_count == 0:
                self._logger.info(
                    "chunk_empty run_id=%s chunk_index=%d", execution_id, chunk.index
                )
                continue

            self._process_with_retry(chunk, execution_id)
            chunks_processed += 1
            rows_processed += chunk.row_count

        finished_at = datetime.now(UTC)
        summary = PipelineSummary(
            run_id=execution_id,
            chunks_processed=chunks_processed,
            rows_processed=rows_processed,
            started_at=started_at,
            finished_at=finished_at,
        )
        self._logger.info(
            "pipeline_success run_id=%s chunks=%d rows=%d elapsed_seconds=%.3f",
            summary.run_id,
            summary.chunks_processed,
            summary.rows_processed,
            summary.elapsed_seconds,
        )
        return summary

    def _process_with_retry(self, chunk: AthenaChunk, run_id: str) -> None:
        policy = self._retry_policy

        for attempt in range(1, policy.max_attempts + 1):
            started = time.monotonic()
            try:
                self._processor.process(chunk)
            except Exception as exc:
                if attempt == policy.max_attempts:
                    self._logger.exception(
                        "chunk_failed run_id=%s chunk_index=%d rows=%d attempts=%d key=%s",
                        run_id,
                        chunk.index,
                        chunk.row_count,
                        attempt,
                        chunk.idempotency_key,
                    )
                    raise ChunkProcessingError(chunk, attempt) from exc

                delay = policy.delay_after_failure(attempt)
                self._logger.warning(
                    "chunk_retry run_id=%s chunk_index=%d attempt=%d delay_seconds=%.3f "
                    "error_type=%s key=%s",
                    run_id,
                    chunk.index,
                    attempt,
                    delay,
                    type(exc).__name__,
                    chunk.idempotency_key,
                )
                self._sleep(delay)
            else:
                self._logger.info(
                    "chunk_success run_id=%s chunk_index=%d rows=%d attempt=%d "
                    "elapsed_seconds=%.3f key=%s",
                    run_id,
                    chunk.index,
                    chunk.row_count,
                    attempt,
                    time.monotonic() - started,
                    chunk.idempotency_key,
                )
                return

