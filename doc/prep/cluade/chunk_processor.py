"""Camada de processamento: contrato (Protocol) + implementação concreta.

O Protocol permite trocar o processamento sem tocar no pipeline
(Strategy pattern com duck typing estrutural do Python 3.12).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ChunkResult:
    """Resultado leve por chunk — nunca guarde o DataFrame aqui,
    ou você perde o benefício de memória do generator."""

    chunk_index: int
    rows_in: int
    rows_out: int


class ChunkProcessor(Protocol):
    """Contrato: qualquer classe com este método serve ao pipeline."""

    def process(self, chunk: pd.DataFrame, chunk_index: int) -> ChunkResult: ...


class MyBusinessProcessor:
    """Implementação concreta — substitua pelo seu processamento real.

    Regras:
    - Opere no chunk e persista/emita o resultado AQUI (S3, banco, fila...).
    - Não acumule DataFrames em atributos da classe.
    """

    def process(self, chunk: pd.DataFrame, chunk_index: int) -> ChunkResult:
        rows_in = len(chunk)

        # >>> seu processamento (idêntico para todos os chunks) <<<
        processed = chunk  # placeholder

        # >>> persistência do resultado do chunk (ex.: wr.s3.to_parquet) <<<

        return ChunkResult(chunk_index=chunk_index, rows_in=rows_in, rows_out=len(processed))
