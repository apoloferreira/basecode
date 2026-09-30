"""Escrita de arquivos diretamente em prefixos do S3."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Literal

from pyspark.sql import DataFrame

from writers.base import BaseWriter

WriteMode = Literal["overwrite", "append", "error", "ignore"]


@dataclass(frozen=True)
class S3FileWriter(BaseWriter):
    """Escrita de arquivos com ``DataFrame.write``.

    Classe intermediária: as subclasses definem ``file_format`` e, se necessário,
    ``default_options``.

    Com ``mode="overwrite"`` e ``partition_by`` preenchido, apenas as partições presentes no
    DataFrame são substituídas (a sessão usa ``partitionOverwriteMode=dynamic``).
    Sem ``partition_by``, ``overwrite`` substitui o prefixo inteiro.
    """

    path: str
    mode: WriteMode = "overwrite"
    partition_by: list[str] = field(default_factory=list)
    options: dict[str, str] = field(default_factory=dict)

    file_format: ClassVar[str]
    default_options: ClassVar[dict[str, str]] = {}

    def __post_init__(self) -> None:
        if not hasattr(type(self), "file_format"):
            raise TypeError(f"{type(self).__name__} deve definir o atributo de classe 'file_format'.")

    def write(self, df_output: DataFrame) -> None:
        writer = (
            df_output.write.format(self.file_format)
            .mode(self.mode)
            .options(**{**self.default_options, **self.options})
        )
        if self.partition_by:
            writer = writer.partitionBy(*self.partition_by)
        writer.save(self.path)


class S3ParquetWriter(S3FileWriter):
    file_format = "parquet"
    default_options = {"compression": "snappy"}


class S3JsonWriter(S3FileWriter):
    file_format = "json"
    default_options = {"compression": "gzip"}


class S3CsvWriter(S3FileWriter):
    file_format = "csv"
    default_options = {"header": "true"}
