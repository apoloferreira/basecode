"""Leitura de arquivos diretamente em prefixos do S3."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import StructType

from readers.base import BaseReader


@dataclass(frozen=True)
class S3FileReader(BaseReader):
    """Leitura de arquivos com ``spark.read``.

    Classe intermediária: as subclasses definem ``file_format`` e, se necessário,
    ``default_options``. As ``options`` do construtor sobrescrevem as ``default_options``.
    """

    spark: SparkSession
    path: str | list[str]
    schema: StructType | None = None
    options: dict[str, str] = field(default_factory=dict)

    file_format: ClassVar[str]
    default_options: ClassVar[dict[str, str]] = {}

    def __post_init__(self) -> None:
        if not hasattr(type(self), "file_format"):
            raise TypeError(f"{type(self).__name__} deve definir o atributo de classe 'file_format'.")

    def read(self) -> DataFrame:
        reader = self.spark.read.format(self.file_format).options(
            **{**self.default_options, **self.options}
        )
        if self.schema is not None:
            reader = reader.schema(self.schema)
        return reader.load(self.path)


class S3ParquetReader(S3FileReader):
    file_format = "parquet"


class S3JsonReader(S3FileReader):
    """JSON Lines (um objeto por linha) por padrão.

    Para arquivos com um único documento ou array JSON, use ``options={"multiLine": "true"}``.
    """

    file_format = "json"


class S3CsvReader(S3FileReader):
    file_format = "csv"
    default_options = {"header": "true", "inferSchema": "false"}
