"""Classe base das escritas."""
from __future__ import annotations

from abc import ABC, abstractmethod

from pyspark.sql import DataFrame


class BaseWriter(ABC):
    """Base de toda escrita: o DataFrame é persistido no destino por ``write(df_output)``."""

    @abstractmethod
    def write(self, df_output: DataFrame) -> None:
        """Persiste o DataFrame no destino."""
