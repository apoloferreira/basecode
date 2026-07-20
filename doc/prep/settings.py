"""Configuração central da aplicação.

Carrega de variáveis de ambiente para funcionar bem em Batch/Lambda/ECS
sem hardcode. Frozen dataclass = imutável e seguro para passar entre camadas.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AthenaSettings:
    database: str
    workgroup: str
    s3_output: str
    # int  -> chunks com tamanho fixo de N linhas (previsível p/ memória)
    # True -> chunks no tamanho em que chegam do Athena (mais rápido, tamanho variável)
    chunksize: int | bool = 100_000
    # CTAS é mais performático para resultados grandes (lê Parquet em vez de CSV)
    ctas_approach: bool = True

    @classmethod
    def from_env(cls) -> "AthenaSettings":
        return cls(
            database=os.environ["ATHENA_DATABASE"],
            workgroup=os.environ.get("ATHENA_WORKGROUP", "primary"),
            s3_output=os.environ["ATHENA_S3_OUTPUT"],
            chunksize=int(os.environ.get("CHUNKSIZE", "100000")),
            ctas_approach=os.environ.get("CTAS_APPROACH", "true").lower() == "true",
        )
