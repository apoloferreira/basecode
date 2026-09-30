"""Escrita em tabelas registradas no Glue Data Catalog."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pyspark.sql import DataFrame, SparkSession

from writers.base import BaseWriter

IcebergWriteMode = Literal["append", "overwrite_partitions"]


@dataclass(frozen=True)
class GlueCatalogTableWriter(BaseWriter):
    """Escreve em uma tabela já existente no Glue Data Catalog (Parquet/Hive) via ``insertInto``.

    Requer o parâmetro de job ``--enable-glue-datacatalog``. A tabela deve ser criada fora do job
    (IaC ou crawler).

    ``insertInto`` associa colunas por posição, não por nome; por isso o DataFrame é reordenado
    conforme o schema da tabela antes da escrita. Com ``overwrite=True`` e a sessão em
    ``partitionOverwriteMode=dynamic``, apenas as partições presentes no DataFrame são substituídas.
    """

    spark: SparkSession
    database: str
    table: str
    overwrite: bool = True

    def write(self, df_output: DataFrame) -> None:
        target = f"{self.database}.{self.table}"
        target_columns = self.spark.table(target).columns
        df_output.select(*target_columns).write.insertInto(target, overwrite=self.overwrite)


@dataclass(frozen=True)
class IcebergTableWriter(BaseWriter):
    """Escreve em uma tabela Iceberg existente no Glue Data Catalog (colunas associadas por nome).

    Requer a sessão criada com ``iceberg_spark_conf(...)`` e o parâmetro de job
    ``--datalake-formats iceberg``.

    Modos:
      - ``overwrite_partitions`` (padrão): substitui as partições presentes no DataFrame;
      - ``append``: acrescenta linhas.
    """

    database: str
    table: str
    mode: IcebergWriteMode = "overwrite_partitions"
    catalog_name: str = "glue_catalog"

    def write(self, df_output: DataFrame) -> None:
        writer = df_output.writeTo(f"{self.catalog_name}.{self.database}.{self.table}")
        if self.mode == "overwrite_partitions":
            writer.overwritePartitions()
        elif self.mode == "append":
            writer.append()
        else:
            raise ValueError(f"Modo de escrita Iceberg não suportado: {self.mode!r}")
