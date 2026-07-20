"""Camada de extração: encapsula o awswrangler e expõe um generator de chunks."""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from typing import Any

import awswrangler as wr
import boto3
import pandas as pd

from app.settings import AthenaSettings

logger = logging.getLogger(__name__)


class AthenaChunkReader:
    """Executa uma query no Athena e entrega o resultado em chunks (lazy).

    A sessão boto3 é injetada para facilitar testes e permitir
    assume-role / região customizada em produção.
    """

    def __init__(
        self,
        settings: AthenaSettings,
        boto3_session: boto3.Session | None = None,
    ) -> None:
        self._settings = settings
        self._session = boto3_session or boto3.Session()

    def iter_chunks(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
    ) -> Iterator[pd.DataFrame]:
        """Generator que produz um DataFrame por chunk.

        A query só é executada quando o primeiro chunk é consumido,
        e cada chunk é descartável após o processamento — a memória
        residente fica limitada a ~1 chunk por vez.
        """
        logger.info(
            "Iniciando query no Athena | database=%s workgroup=%s chunksize=%s",
            self._settings.database,
            self._settings.workgroup,
            self._settings.chunksize,
        )
        started = time.perf_counter()

        chunks = wr.athena.read_sql_query(
            sql=sql,
            database=self._settings.database,
            workgroup=self._settings.workgroup,
            s3_output=self._settings.s3_output,
            ctas_approach=self._settings.ctas_approach,
            chunksize=self._settings.chunksize,
            params=params,
            paramstyle="named",
            boto3_session=self._session,
        )

        total_rows = 0
        for index, chunk in enumerate(chunks):
            total_rows += len(chunk)
            logger.info(
                "Chunk %d recebido | linhas=%d | acumulado=%d",
                index, len(chunk), total_rows,
            )
            yield chunk

        elapsed = time.perf_counter() - started
        logger.info(
            "Query concluída | chunks=%d linhas=%d tempo=%.1fs",
            index + 1 if total_rows else 0, total_rows, elapsed,
        )
