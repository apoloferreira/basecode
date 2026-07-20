"""Orquestração: consome o generator do reader e delega ao processor.

Padrão: Pipeline/Orchestrator. É a única camada que conhece reader E processor,
mas depende de ambos por abstração (injeção via construtor).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.extract.athena_reader import AthenaChunkReader
from app.process.chunk_processor import ChunkProcessor, ChunkResult

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PipelineReport:
    chunks_ok: int = 0
    chunks_failed: int = 0
    rows_processed: int = 0
    failed_indexes: list[int] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.chunks_failed == 0


class ChunkPipeline:
    def __init__(
        self,
        reader: AthenaChunkReader,
        processor: ChunkProcessor,
        fail_fast: bool = True,
    ) -> None:
        self._reader = reader
        self._processor = processor
        self._fail_fast = fail_fast

    def run(self, sql: str, params: dict[str, Any] | None = None) -> PipelineReport:
        report = PipelineReport()

        for index, chunk in enumerate(self._reader.iter_chunks(sql, params)):
            try:
                result: ChunkResult = self._processor.process(chunk, index)
            except Exception:
                report.chunks_failed += 1
                report.failed_indexes.append(index)
                logger.exception("Falha no chunk %d", index)
                if self._fail_fast:
                    raise
                continue

            report.chunks_ok += 1
            report.rows_processed += result.rows_out
            # `chunk` sai de escopo aqui e é coletado antes do próximo yield

        logger.info(
            "Pipeline finalizado | ok=%d falhas=%d linhas=%d",
            report.chunks_ok, report.chunks_failed, report.rows_processed,
        )
        return report
