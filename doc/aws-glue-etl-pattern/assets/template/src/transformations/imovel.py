"""Domínio imóvel rural: atributos cadastrais do imóvel."""
from __future__ import annotations

from pyspark.sql import DataFrame

from transformations.common import normalize_column_names


def select_atributos_imovel(df_imoveis: DataFrame) -> DataFrame:
    """Seleciona os atributos de localização do imóvel, uma linha por imóvel."""
    return (
        df_imoveis.transform(normalize_column_names)
        .select("cod_imovel", "municipio", "uf")
        .dropDuplicates(["cod_imovel"])
    )


def enrich_with_imovel(df_input: DataFrame, df_imoveis: DataFrame) -> DataFrame:
    """Adiciona município e UF pela chave ``cod_imovel``. Imóveis sem cadastro ficam com atributos nulos."""
    return df_input.join(select_atributos_imovel(df_imoveis), on="cod_imovel", how="left")
