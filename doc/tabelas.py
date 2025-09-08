import sys
import os
import pyarrow as pa
import pandas as pd
import awswrangler as wr
from dataclasses import dataclass
from pyiceberg.catalog import load_catalog
from pyiceberg.table import DataScan
from pyiceberg.table import Table

sys.path.append(os.getcwd())
import constantes as const
from base import PATable, Record
from exceptions import PrimaryKeyDuplicatedError, RecordNotFoundError


@dataclass
class ControleIngestao(Record):
    id_poligono: str
    data_penultima_ingestao: str
    data_ultima_ingestao: str

@dataclass
class ControleImagem(Record):
    id_poligono: str
    poligono: str
    area_poligono: str # mudar para pixels_imagem
    caminho_s3: str

@dataclass
class Imagem(Record):
    id_poligono: str
    data_imagem: str
    no_data: float
    saturated_or_defective: float
    dark_area_pixels: float
    cloud_shadows: float
    vegetation: float
    bare_soils: float
    water: float
    clouds_low_probability_or_unclassified: float
    clouds_medium_probability: float
    clouds_high_probability: float
    thin_cirrus: float
    snow_or_ice: float


class PATableControleIngestao(PATable):
    schema: pa.schema = pa.schema([
        pa.field("id_poligono", pa.string(), nullable=False),
        pa.field("data_penultima_ingestao", pa.string(), nullable=True),
        pa.field("data_ultima_ingestao", pa.string(), nullable=False),
    ])

class PATableControleImagem(PATable):
    schema: pa.schema = pa.schema([
        pa.field("id_poligono", pa.string(), nullable=False),
        pa.field("poligono", pa.string(), nullable=False),
        pa.field("area_poligono", pa.string(), nullable=True),
        pa.field("caminho_s3", pa.string(), nullable=True),
    ])

class PATableImagem(PATable):
    schema: pa.schema = pa.schema([
        pa.field("id_poligono", pa.string(), nullable=False),
        pa.field("data_imagem", pa.string(), nullable=False),
        pa.field("no_data", pa.float32(), nullable=True),
        pa.field("saturated_or_defective", pa.float32(), nullable=True),
        pa.field("dark_area_pixels", pa.float32(), nullable=True),
        pa.field("cloud_shadows", pa.float32(), nullable=True),
        pa.field("vegetation", pa.float32(), nullable=True),
        pa.field("bare_soils", pa.float32(), nullable=True),
        pa.field("water", pa.float32(), nullable=True),
        pa.field("clouds_low_probability_or_unclassified", pa.float32(), nullable=True),
        pa.field("clouds_medium_probability", pa.float32(), nullable=True),
        pa.field("clouds_high_probability", pa.float32(), nullable=True),
        pa.field("thin_cirrus", pa.float32(), nullable=True),
        pa.field("snow_or_ice", pa.float32(), nullable=True),
    ])


class IcebergTable:

    def __init__(self, table: Table, record_class: Record) -> None:
        self.table = table
        self.record_class = record_class

    def load_record(self, record_id: int) -> DataScan:
        return self.table.scan(row_filter=f"id_poligono == '{record_id}'")

    def get_record(self, record_id: int) -> Record:
        tb_arrow = self.load_record(record_id).to_arrow()
        if tb_arrow.num_rows == 0:
            raise RecordNotFoundError(f"No record found with id '{record_id}'")
        if tb_arrow.num_rows > 1:
            raise PrimaryKeyDuplicatedError(f"Polygon Id duplicated with id '{record_id}'")
        return self.record_class(
            **{
                key: value[0] for key, value 
                in tb_arrow.to_pydict().items()
            }
        )

    def upsert(self, pyarrow_table: PATable) -> None:
        self.table.upsert(
            df=pyarrow_table.to_pyarrow_table(),
            join_cols=["id_poligono"]
        )

    def append(self, pyarrow_table: PATable) -> None:
        self.table.append(df=pyarrow_table.to_pyarrow_table())

    def record_exist(self, record_id: int) -> bool:
        tb_arrow = self.load_record(record_id).to_arrow()
        if tb_arrow.num_rows > 0:
            return True
        return False


class IcebergFactory:

    glue_catalog = load_catalog(
        'default',
        type='glue',
        profile='default',
        region_name=const.REGION,
        client={
            'region': const.REGION,
        }
    )

    @classmethod
    def load_iceberg_table(cls, database: str, table: str, record_class: Record) -> IcebergTable:
        table = cls.glue_catalog.load_table((database, table))
        return IcebergTable(table, record_class)


def athena_read_sql(query: str) -> pd.DataFrame:
    return wr.athena.read_sql_query(
        sql=query,
        database=const.DATABASE,
        ctas_approach=False,
        s3_output=const.S3_ATHENA_OUTPUT
    )

