"""Classe base das leituras."""
from __future__ import annotations

from abc import ABC, abstractmethod

from pyspark.sql import DataFrame


class BaseReader(ABC):
    """Base de toda leitura: a fonte é lida por ``read()``, que devolve um DataFrame."""

    @abstractmethod
    def read(self) -> DataFrame:
        """Lê a fonte e devolve um DataFrame."""
