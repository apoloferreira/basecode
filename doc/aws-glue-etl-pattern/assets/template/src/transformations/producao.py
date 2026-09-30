"""Domínio produção agrícola: indicadores de área plantada."""
from __future__ import annotations

from dataclasses import dataclass

from pyspark.sql import DataFrame

from transformations.base import BaseTransformation
from transformations.common import add_processing_metadata
from transformations.imovel import enrich_with_imovel
from transformations.talhao import area_por_cultura

OUTPUT_COLUMNS = [
    "cod_imovel",
    "municipio",
    "uf",
    "cultura",
    "area_plantada_ha",
    "qtd_talhoes",
    "processed_at",
    "dt",
]


@dataclass(frozen=True)
class AreaPlantadaPorImovel(BaseTransformation):
    """Área plantada e quantidade de talhões por imóvel rural e cultura.

    Espera talhões já limpos (saída de ``transformations.talhao.clean_talhoes``).

    Args:
        casas_decimais: precisão do arredondamento de ``area_plantada_ha``.
    """

    casas_decimais: int = 4

    def transform(
        self, df_imoveis: DataFrame, df_talhoes: DataFrame, reference_date: str
    ) -> DataFrame:
        return (
            df_talhoes.transform(area_por_cultura, casas_decimais=self.casas_decimais)
            .transform(enrich_with_imovel, df_imoveis=df_imoveis)
            .transform(add_processing_metadata, reference_date=reference_date)
            .select(*OUTPUT_COLUMNS)
        )
