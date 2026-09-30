"""Transformações genéricas, sem regra de negócio de nenhum domínio."""
from __future__ import annotations

import re
import unicodedata
from typing import Sequence

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F


def _to_snake_case(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^0-9a-zA-Z]+", "_", ascii_name).strip("_").lower()


def normalize_column_names(df_input: DataFrame) -> DataFrame:
    """Converte os nomes das colunas para snake_case sem acentos (ex.: ``"Área (ha)"`` -> ``"area_ha"``)."""
    return df_input.toDF(*[_to_snake_case(column) for column in df_input.columns])


def deduplicate(df_input: DataFrame, keys: Sequence[str], order_by: str | None = None) -> DataFrame:
    """Mantém uma linha por chave.

    Com ``order_by``, mantém a linha com o maior valor da coluna (ex.: o registro mais recente);
    sem ele, a escolha entre duplicatas é arbitrária.
    """
    if order_by is None:
        return df_input.dropDuplicates(list(keys))
    window = Window.partitionBy(*keys).orderBy(F.col(order_by).desc())
    return (
        df_input.withColumn("_row_number", F.row_number().over(window))
        .where(F.col("_row_number") == 1)
        .drop("_row_number")
    )


def add_processing_metadata(
    df_input: DataFrame, reference_date: str, partition_column: str = "dt"
) -> DataFrame:
    """Adiciona a coluna de partição (data de referência) e o timestamp de processamento."""
    return df_input.withColumn(partition_column, F.lit(reference_date)).withColumn(
        "processed_at", F.current_timestamp()
    )
