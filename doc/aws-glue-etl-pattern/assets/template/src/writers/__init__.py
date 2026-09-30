"""Classes de escrita. Todas herdam de BaseWriter e expõem ``write(df_output) -> None``."""
from writers.base import BaseWriter
from writers.catalog import GlueCatalogTableWriter, IcebergTableWriter
from writers.s3 import S3CsvWriter, S3FileWriter, S3JsonWriter, S3ParquetWriter

__all__ = [
    "BaseWriter",
    "GlueCatalogTableWriter",
    "IcebergTableWriter",
    "S3CsvWriter",
    "S3FileWriter",
    "S3JsonWriter",
    "S3ParquetWriter",
]
