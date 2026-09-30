"""Domínio talhão: limpeza e agregações de talhões agrícolas."""
from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from transformations.common import deduplicate, normalize_column_names


def clean_talhoes(df_talhoes: DataFrame, area_minima_ha: float = 0.0) -> DataFrame:
    """Padroniza colunas, descarta talhões com área menor ou igual a ``area_minima_ha``
    e mantém a versão mais recente de cada talhão."""
    return (
        df_talhoes.transform(normalize_column_names)
        .where(F.col("area_ha").isNotNull() & (F.col("area_ha") > area_minima_ha))
        .withColumn("cultura", F.lower(F.trim(F.col("cultura"))))
        .transform(deduplicate, keys=["id_talhao"], order_by="atualizado_em")
    )


def area_por_cultura(df_talhoes: DataFrame, casas_decimais: int = 4) -> DataFrame:
    """Soma a área plantada e conta talhões por imóvel e cultura."""
    return df_talhoes.groupBy("cod_imovel", "cultura").agg(
        F.round(F.sum("area_ha"), casas_decimais).alias("area_plantada_ha"),
        F.count("id_talhao").alias("qtd_talhoes"),
    )
