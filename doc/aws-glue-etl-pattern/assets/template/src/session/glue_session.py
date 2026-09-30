"""Criação da sessão Spark e dos objetos do Glue (GlueContext e Job)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import SparkSession

DEFAULT_SPARK_CONF: dict[str, str] = {
    # Adaptive Query Execution: reotimiza o plano em tempo de execução
    "spark.sql.adaptive.enabled": "true",
    "spark.sql.adaptive.coalescePartitions.enabled": "true",
    "spark.sql.adaptive.skewJoin.enabled": "true",
    # conversões Spark <-> pandas via Arrow
    "spark.sql.execution.arrow.pyspark.enabled": "true",
    # datas/timestamps antigos em Parquet e parsing de datas sem conversão de calendário legado
    "spark.sql.parquet.datetimeRebaseModeInRead": "CORRECTED",
    "spark.sql.parquet.datetimeRebaseModeInWrite": "CORRECTED",
    "spark.sql.legacy.timeParserPolicy": "CORRECTED",
    # overwrite + partitionBy substitui só as partições presentes no DataFrame
    "spark.sql.sources.partitionOverwriteMode": "dynamic",
    # insertInto com partições dinâmicas em tabelas Hive/Glue Data Catalog
    "hive.exec.dynamic.partition": "true",
    "hive.exec.dynamic.partition.mode": "nonstrict",
}


def build_spark_conf(extra_conf: Mapping[str, str] | None = None) -> dict[str, str]:
    """Une ``DEFAULT_SPARK_CONF`` com ``extra_conf``; em chaves repetidas, prevalece ``extra_conf``."""
    return {**DEFAULT_SPARK_CONF, **(extra_conf or {})}


def iceberg_spark_conf(warehouse_path: str, catalog_name: str = "glue_catalog") -> dict[str, str]:
    """Configurações para usar tabelas Iceberg no Glue Data Catalog.

    Passe o resultado em ``spark_conf`` de ``create_spark_session`` ou ``create_glue_session``.
    O job também precisa do parâmetro ``--datalake-formats iceberg``.
    """
    prefix = f"spark.sql.catalog.{catalog_name}"
    return {
        "spark.sql.extensions": "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
        prefix: "org.apache.iceberg.spark.SparkCatalog",
        f"{prefix}.warehouse": warehouse_path,
        f"{prefix}.catalog-impl": "org.apache.iceberg.aws.glue.GlueCatalog",
        f"{prefix}.io-impl": "org.apache.iceberg.aws.s3.S3FileIO",
    }


def create_spark_session(
    app_name: str,
    spark_conf: Mapping[str, str] | None = None,
    enable_hive_support: bool = True,
) -> SparkSession:
    """Cria a SparkSession com ``DEFAULT_SPARK_CONF`` mais as configurações de ``spark_conf``.

    Args:
        app_name: nome da aplicação Spark (normalmente o nome do job).
        spark_conf: configurações adicionais; sobrescrevem as padrão quando a chave já existe.
        enable_hive_support: habilita o metastore Hive, necessário para acessar o Glue Data
            Catalog via ``spark.table`` e ``insertInto``.
    """
    builder = SparkSession.builder.appName(app_name)
    for key, value in build_spark_conf(spark_conf).items():
        builder = builder.config(key, value)
    if enable_hive_support:
        builder = builder.enableHiveSupport()
    return builder.getOrCreate()


@dataclass(frozen=True)
class GlueSession:
    """Objetos de sessão distribuídos pelo main.py para leitores e escritores."""

    spark: SparkSession
    glue_context: GlueContext
    job: Job

    def commit(self) -> None:
        """Confirma a execução. Com job bookmarks habilitados, avança o bookmark."""
        self.job.commit()


def create_glue_session(
    job_name: str,
    job_args: Mapping[str, str | None],
    spark_conf: Mapping[str, str] | None = None,
    enable_hive_support: bool = True,
) -> GlueSession:
    """Cria a SparkSession (via ``create_spark_session``) e, sobre ela, o GlueContext e o Job.

    Args:
        job_name: nome do job (``args["JOB_NAME"]``).
        job_args: parâmetros resolvidos do job (usados pelo Job para bookmarks).
        spark_conf: configurações Spark adicionais do job; sobrescrevem as padrão.
        enable_hive_support: repassado para ``create_spark_session``.
    """
    spark = create_spark_session(
        app_name=job_name,
        spark_conf=spark_conf,
        enable_hive_support=enable_hive_support,
    )
    glue_context = GlueContext(spark.sparkContext)
    job = Job(glue_context)
    job.init(job_name, dict(job_args))
    return GlueSession(spark=spark, glue_context=glue_context, job=job)
