"""Leitura de tabelas registradas no Glue Data Catalog."""
from __future__ import annotations

from dataclasses import dataclass, field

from awsglue.context import GlueContext
from pyspark.sql import DataFrame, SparkSession

from readers.base import BaseReader


@dataclass(frozen=True)
class GlueCatalogReader(BaseReader):
    """Lê uma tabela do Glue Data Catalog via DynamicFrame e devolve um DataFrame.

    Usa o GlueContext (e não ``spark.table``) para respeitar as permissões do Lake Formation,
    permitir push down de partições e habilitar job bookmarks (via ``transformation_ctx``).

    Args:
        push_down_predicate: filtro de partições aplicado antes da listagem no S3,
            ex.: ``"dt = '2026-09-30'"``.
        transformation_ctx: identificador único da leitura no job; obrigatório para bookmarks.
    """

    glue_context: GlueContext
    database: str
    table: str
    push_down_predicate: str = ""
    transformation_ctx: str = ""
    additional_options: dict[str, str] = field(default_factory=dict)

    def read(self) -> DataFrame:
        dynamic_frame = self.glue_context.create_dynamic_frame.from_catalog(
            database=self.database,
            table_name=self.table,
            push_down_predicate=self.push_down_predicate,
            transformation_ctx=self.transformation_ctx,
            additional_options=self.additional_options,
        )
        return dynamic_frame.toDF()


@dataclass(frozen=True)
class IcebergTableReader(BaseReader):
    """Lê uma tabela Iceberg registrada no Glue Data Catalog.

    Requer a sessão criada com ``iceberg_spark_conf(...)`` e o parâmetro de job
    ``--datalake-formats iceberg``.

    Args:
        where: filtro SQL aplicado na leitura (o Iceberg faz o pruning de partições e arquivos).
    """

    spark: SparkSession
    database: str
    table: str
    where: str | None = None
    catalog_name: str = "glue_catalog"

    def read(self) -> DataFrame:
        df_table = self.spark.table(f"{self.catalog_name}.{self.database}.{self.table}")
        return df_table.where(self.where) if self.where else df_table
