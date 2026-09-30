"""Classe base das transformações implementadas como classe."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pyspark.sql import DataFrame


class BaseTransformation(ABC):
    """Base das transformações em classe: recebe DataFrames de entrada e devolve o DataFrame resultante.

    Os parâmetros de configuração da transformação ficam nos atributos da instância;
    os DataFrames de entrada são passados para ``transform``.
    """

    @abstractmethod
    def transform(self, *args: Any, **kwargs: Any) -> DataFrame:
        """Aplica a transformação e devolve o DataFrame resultante."""
