from __future__ import annotations

import logging
import os

import pandas as pd

from .athena_reader import AthenaChunkReader
from .config import AthenaSettings
from .pipeline import ChunkPipeline, RetryPolicy
from .processors import TransformAndWriteProcessor


def transform(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Substitua pela transformacao deterministica da sua regra de negocio."""
    return dataframe


def write_result(dataframe: pd.DataFrame, idempotency_key: str) -> None:
    """Substitua por um destino idempotente (S3, banco, API etc.)."""
    logging.getLogger(__name__).info(
        "example_sink rows=%d idempotency_key=%s", len(dataframe.index), idempotency_key
    )


def _retry_policy_from_env() -> RetryPolicy:
    return RetryPolicy(
        max_attempts=int(os.getenv("PROCESSING_MAX_ATTEMPTS", "3")),
        initial_delay_seconds=float(os.getenv("PROCESSING_INITIAL_DELAY_SECONDS", "1.0")),
        backoff_multiplier=float(os.getenv("PROCESSING_BACKOFF_MULTIPLIER", "2.0")),
        max_delay_seconds=float(os.getenv("PROCESSING_MAX_DELAY_SECONDS", "30.0")),
    )


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    sql = os.getenv("ATHENA_SQL", "").strip()
    if not sql:
        raise ValueError("A variavel de ambiente ATHENA_SQL e obrigatoria")

    reader = AthenaChunkReader(AthenaSettings.from_env())
    processor = TransformAndWriteProcessor(transform=transform, sink=write_result)
    pipeline = ChunkPipeline(reader, processor, retry_policy=_retry_policy_from_env())
    pipeline.run(sql)


if __name__ == "__main__":
    main()

