"""Entrypoint do job Glue: controla o fluxo extract -> transform -> load.

Parâmetros do job:
    --JOB_NAME            preenchido pelo Glue
    --REFERENCE_DATE      data processada, YYYY-MM-DD (partição de leitura e de escrita)
    --IMOVEIS_DATABASE    database do Glue Data Catalog com a tabela de imóveis (padrão: cadastro)
    --IMOVEIS_TABLE       tabela de imóveis particionada por dt (padrão: imoveis)
    --TALHOES_PATH        prefixo S3 dos JSON de talhões, particionado em dt=YYYY-MM-DD/
    --TARGET_PATH         prefixo S3 de saída (Parquet particionado por dt)
    --TALHOES_MULTILINE   opcional, "true" se cada arquivo for um único documento/array JSON (padrão: false)
    --AREA_MINIMA_HA      opcional, área mínima do talhão em hectares (padrão: 0)
    --CASAS_DECIMAIS      opcional, casas decimais da área plantada (padrão: 4)
"""
import sys

from readers import GlueCatalogReader, S3JsonReader
from session import create_glue_session
from transformations.producao import AreaPlantadaPorImovel
from transformations.talhao import clean_talhoes
from utils import JobArg, get_job_args, get_logger
from writers import S3ParquetWriter

JOB_ARGS = [
    JobArg("REFERENCE_DATE"),
    JobArg("IMOVEIS_DATABASE", default="cadastro"),
    JobArg("IMOVEIS_TABLE", default="imoveis"),
    JobArg("TALHOES_PATH"),
    JobArg("TARGET_PATH"),
    JobArg("TALHOES_MULTILINE", required=False, default="false"),
    JobArg("AREA_MINIMA_HA", required=False, default="0"),
    JobArg("CASAS_DECIMAIS", required=False, default="4"),
]

SPARK_CONF = {
    "spark.sql.shuffle.partitions": "64",
    "spark.sql.adaptive.advisoryPartitionSizeInBytes": "128m",
    "spark.sql.execution.arrow.pyspark.enabled": "false",
}


def main() -> None:
    args = get_job_args(sys.argv, JOB_ARGS)
    logger = get_logger(args["JOB_NAME"])
    session = create_glue_session(
        job_name=args["JOB_NAME"],
        job_args=args,
        spark_conf=SPARK_CONF,
    )
    reference_date = args["REFERENCE_DATE"]

    logger.info("Início do job | reference_date=%s", reference_date)
    try:
        # 1. Extract --------------------------------------------------------------
        df_imoveis = GlueCatalogReader(
            glue_context=session.glue_context,
            database=args["IMOVEIS_DATABASE"],
            table=args["IMOVEIS_TABLE"],
            push_down_predicate=f"dt = '{reference_date}'",
        ).read()

        df_talhoes = S3JsonReader(
            spark=session.spark,
            path=f"{args['TALHOES_PATH'].rstrip('/')}/dt={reference_date}/",
            options={"multiLine": args["TALHOES_MULTILINE"]},
        ).read()

        # 2. Transform ------------------------------------------------------------
        df_talhoes_validos = clean_talhoes(
            df_talhoes,
            area_minima_ha=float(args["AREA_MINIMA_HA"]),
        )

        df_area_plantada = AreaPlantadaPorImovel(
            casas_decimais=int(args["CASAS_DECIMAIS"]),
        ).transform(
            df_imoveis=df_imoveis,
            df_talhoes=df_talhoes_validos,
            reference_date=reference_date,
        )

        # 3. Load -----------------------------------------------------------------
        S3ParquetWriter(
            path=args["TARGET_PATH"],
            partition_by=["dt"],
        ).write(df_area_plantada)

    except Exception:
        logger.exception("Falha no job | reference_date=%s", reference_date)
        raise

    session.commit()
    logger.info("Fim do job | reference_date=%s", reference_date)


if __name__ == "__main__":
    main()
