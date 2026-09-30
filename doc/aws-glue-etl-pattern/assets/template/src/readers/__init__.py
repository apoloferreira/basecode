"""Classes de leitura. Todas herdam de BaseReader e expõem ``read() -> DataFrame``."""
from readers.base import BaseReader
from readers.catalog import GlueCatalogReader, IcebergTableReader
from readers.s3 import S3CsvReader, S3FileReader, S3JsonReader, S3ParquetReader

__all__ = [
    "BaseReader",
    "GlueCatalogReader",
    "IcebergTableReader",
    "S3CsvReader",
    "S3FileReader",
    "S3JsonReader",
    "S3ParquetReader",
]
