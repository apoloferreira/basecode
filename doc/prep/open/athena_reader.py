from __future__ import annotations

import logging
from collections.abc import Callable, Iterator, Mapping
from typing import Any

import pandas as pd

from .config import AthenaSettings
from .models import AthenaChunk

QueryExecutor = Callable[..., pd.DataFrame | Iterator[pd.DataFrame]]


def _default_query_executor() -> QueryExecutor:
    # Import tardio: facilita testes unitarios sem carregar o SDK da AWS.
    import awswrangler as wr

    return wr.athena.read_sql_query


class AthenaChunkReader:
    """Adapter entre awswrangler e o contrato de chunks da aplicacao."""

    def __init__(
        self,
        settings: AthenaSettings,
        *,
        boto3_session: Any | None = None,
        query_executor: QueryExecutor | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._settings = settings
        self._boto3_session = boto3_session
        self._query_executor = query_executor or _default_query_executor()
        self._logger = logger or logging.getLogger(__name__)

    def read_chunks(
        self,
        sql: str,
        *,
        params: Mapping[str, Any] | list[str] | None = None,
    ) -> Iterator[AthenaChunk]:
        ctas_approach, unload_approach = self._settings.approach_flags()

        self._logger.info(
            "athena_query_start database=%s workgroup=%s mode=%s chunk_size=%s",
            self._settings.database,
            self._settings.workgroup,
            self._settings.read_mode,
            self._settings.chunk_size,
        )

        result = self._query_executor(
            sql=sql,
            database=self._settings.database,
            ctas_approach=ctas_approach,
            unload_approach=unload_approach,
            chunksize=self._settings.chunk_size,
            s3_output=self._settings.s3_output,
            workgroup=self._settings.workgroup,
            encryption=self._settings.encryption,
            kms_key=self._settings.kms_key,
            keep_files=self._settings.keep_files,
            use_threads=self._settings.use_threads,
            boto3_session=self._boto3_session,
            athena_query_wait_polling_delay=self._settings.polling_delay_seconds,
            params=params,
            paramstyle="named" if isinstance(params, Mapping) or params is None else "qmark",
        )

        if isinstance(result, pd.DataFrame):
            raise TypeError(
                "read_sql_query retornou DataFrame em vez de Iterator; "
                "verifique se chunksize foi informado"
            )

        for index, dataframe in enumerate(result):
            metadata = getattr(dataframe, "query_metadata", None) or {}
            query_execution_id = metadata.get("QueryExecutionId")
            yield AthenaChunk(
                index=index,
                dataframe=dataframe,
                query_execution_id=query_execution_id,
                query_metadata=metadata,
            )

