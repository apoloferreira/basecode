import sys
import os
import json
import boto3
import pandas as pd
import numpy as np
import xarray as xr
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pystac import Item
from shapely import wkt
from shapely.geometry import Polygon
from xarray import Dataset, DataArray

sys.path.append(os.getcwd())
import constantes as const
from tabelas import athena_read_sql
from imagens import (
    stac_search_images, stac_load_dataset,
    save_s3_zarr, s3_path_exists
)
from tabelas import (
    IcebergFactory, ControleIngestao, ControleImagem, Imagem, 
    PATableControleIngestao, PATableControleImagem, PATableImagem
)
from exceptions import RecordNotFoundError

# def load_records_of_the_day() -> pd.DataFrame:
#     date_reference = datetime.today().strftime("%Y%m%d")
#     query = f"""
#     SELECT *
#     FROM {const.DATABASE}.{const.TABLE_POLIGONO}
#     WHERE anomesdia = {date_reference}
#     """
#     df = athena_read_sql(query)
#     return df


# def filter_records(df: pd.DataFrame) -> pd.DataFrame:
#     df_filtered = df[
#         (df['cod_monitoramento'] == "1") &
#         (df['id_poligono'] != '')
#     ]
#     return df_filtered


def get_polygon_record_by_day(id_poligono: str) -> dict:
    # date_reference = datetime.today().strftime("%Y%m%d")
    query = f"""
    SELECT *
    FROM {const.DATABASE}.{const.TABLE_POLIGONO}
    WHERE id_poligono = '{id_poligono}'
    """ # anomesdia = {date_reference}
    df = athena_read_sql(query)
    try:
        return df.iloc[0, :].to_dict()
    except IndexError:
        return {}
    # return df.iloc[0, :].to_dict()


def convert_polygon(polygon: str) -> Polygon:
    return wkt.loads(polygon)


def less_than_temporal_resolution(last_ingestion: str) -> bool:
    dt_last_ingestion = datetime.strptime(last_ingestion, "%Y-%m-%dT%H:%M:%S.%fZ")
    days_difference = (datetime.today() - dt_last_ingestion).days
    if days_difference < 5:
        return True
    return False


def get_ingestion_record(record_polygon: dict) -> dict:
    icerberg_ingestao = IcebergFactory()\
        .load_iceberg_table(const.DATABASE, const.TABLE_INGESTAO, ControleIngestao)
    try:
        record = icerberg_ingestao.get_record(record_polygon['id_poligono'])
        return record.to_dict()
    except RecordNotFoundError:
        return {
            "id_poligono": record_polygon['id_poligono'],
            "data_penultima_ingestao": None,
            "data_ultima_ingestao": None
        }


def define_start_date(record_polygon: dict, record_ingestion: dict) -> str | None:
    if record_ingestion.get('data_ultima_ingestao'):
        last_ingestion = record_ingestion['data_ultima_ingestao']
        if less_than_temporal_resolution(last_ingestion):
            return None
        return last_ingestion
    dt_plantio = datetime.strptime(record_polygon['data_plantio'], "%Y-%m-%d")
    dt_plantio = dt_plantio - relativedelta(months=1)
    return datetime.strftime(dt_plantio, "%Y-%m-%d")


def search_images(record_polygon: str, start_date: str) -> list:
    polygon = convert_polygon(record_polygon['poligono'])
    response = stac_search_images(polygon, start_date)
    return response


def load_dataset(record_polygon: dict, stac_metadata: list[Item]) -> Dataset:
    polygon = convert_polygon(record_polygon['poligono'])
    return stac_load_dataset(polygon, stac_metadata)


def calculate_spectral_indices(ds: Dataset) -> Dataset:
    # Talvez fazer os calculos somente no poligono ao invez do bbox todo
    ds['ndvi'] = (ds.nir - ds.red) / (ds.nir + ds.red)
    return ds


def scl_count_fc(block, minlength):
    arr = block.ravel()
    if np.issubdtype(arr.dtype, np.floating):
        arr = arr[~np.isnan(arr)]
    if arr.size == 0:
        return np.zeros(minlength, dtype=np.int64)
    return np.bincount(arr.astype(np.int64), minlength=minlength)


def get_total_pixels(da: DataArray) -> int:
    return da.isel(time=0).count(dim=('y','x')).values.item()


def count_classification_pixels(da: DataArray) -> pd.DataFrame:
    total_pixels = get_total_pixels(da)
    n_categories = len(const.CLASSIFICATION_MAP)
    da_counts = xr.apply_ufunc(
        scl_count_fc,
        da,
        kwargs={'minlength': n_categories},
        input_core_dims=[['y','x']],
        output_core_dims=[['category']],
        vectorize=True,
        dask='parallelized',
        output_dtypes=[np.uint32],
        output_sizes={'category': n_categories}
    )
    da_counts = da_counts.assign_coords(category=np.arange(n_categories))
    da_counts = da_counts / total_pixels * 100
    da_counts = da_counts.round(4).astype(np.float16)
    da_counts = da_counts.compute()
    return da_counts.to_pandas()


def format_classification_dataframe(df: pd.DataFrame, id_poligono: str) -> pd.DataFrame:
    df = df.applymap(lambda v: float(f"{v:.2f}"))
    df = df.reset_index()
    df.columns.name = None
    df = df.rename(columns=const.CLASSIFICATION_MAP | {'time': 'data_imagem'})
    df['id_poligono'] = id_poligono
    df['data_imagem'] = df['data_imagem'].dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    new_column_order = ['id_poligono', 'data_imagem'] + list(const.CLASSIFICATION_MAP.values())
    df = df[new_column_order]
    return df


def process_images(ds: Dataset, id_poligono: str) -> pd.DataFrame:
    # TODO: Selecionar somente o poligono. Nao o bbox todo
    ds = calculate_spectral_indices(ds)
    df_scl = count_classification_pixels(ds['scl'])
    df_scl = format_classification_dataframe(df_scl, id_poligono)
    return df_scl


def define_mode(id_poligono: str) -> tuple[str, dict]:
    zarr_path = f"{const.S3_PREFIX_IMAGENS}/{const.SATELLITE_COLLECTION}/{id_poligono}.zarr"
    print(f"Zarr path: {zarr_path}")
    if s3_path_exists(const.S3_BUCKET_IMAGENS, zarr_path):
        mode = "a"
        append_kwargs = {"append_dim": "time"}
    else:
        mode = "w-"
        append_kwargs = {}
    return mode, append_kwargs


def save_images(id_poligono: str, ds: Dataset) -> None:
    mode, append_kwargs = define_mode(id_poligono)
    save_s3_zarr(ds, id_poligono, mode, append_kwargs)


def save_metadata(id_poligono: str, stac_metadata: list[Item]) -> None:
    client_s3 = boto3.client(service_name='s3')
    for item in stac_metadata:
        item_dict = item.to_dict()
        date_reference = item_dict['properties']['datetime'][:19]
        data = {
            "id_poligono": id_poligono,
            "date_image": date_reference, # ou image_date
            "item": item_dict,
        }
        json_data = json.dumps(data)
        full_prefix = f"{const.S3_PREFIX_METADATA}/{id_poligono}/{date_reference}.json"
        try:
            client_s3.put_object(Bucket=const.S3_BUCKET_METADATA, Key=full_prefix, Body=json_data)
            print(f"Successfully saved dictionary as JSON to s3://{const.S3_BUCKET_METADATA}/{full_prefix}")
        except Exception as e:
            print(f"Error saving to S3: {e}")


def generate_image_control_record(record_poligono: dict, area: int) -> dict:
    record_control = {
        "id_poligono": record_poligono['id_poligono'],
        "poligono": record_poligono['poligono'], # Converter poligono para crs do stac
        "area_poligono": str(area),
        "caminho_s3": "/".join([
            f"s3://{const.S3_BUCKET_IMAGENS}/{const.S3_PREFIX_IMAGENS}/{const.SATELLITE_COLLECTION}",
            f"{record_poligono['id_poligono']}.zarr"
        ])
    }
    return record_control


def update_ingestion_record(record_ingestion: dict, start_date: str) -> None:
    icerberg_ingestao = IcebergFactory()\
        .load_iceberg_table(const.DATABASE, const.TABLE_INGESTAO, ControleIngestao)
    pa_table_ingestao = PATableControleIngestao()
    record_ingestion["data_penultima_ingestao"] = record_ingestion["data_ultima_ingestao"]
    record_ingestion["data_ultima_ingestao"] = start_date
    record_ingestao = ControleIngestao(**record_ingestion)
    pa_table_ingestao.add_record(record_ingestao)
    icerberg_ingestao.upsert(pa_table_ingestao)


def insert_image_control_table(record_poligono: dict, number_of_pixles: int) -> None:
    icerberg_controle_imagem = IcebergFactory()\
        .load_iceberg_table(const.DATABASE, const.TABLE_CONTROLE_IMAGEM, ControleImagem)
    if not icerberg_controle_imagem.record_exist(record_poligono['id_poligono']):
        record = generate_image_control_record(record_poligono, number_of_pixles)
        record_imagem = ControleImagem(**record)
        pa_table_controle_imagem = PATableControleImagem()
        pa_table_controle_imagem.add_record(record_imagem)
        icerberg_controle_imagem.upsert(pa_table_controle_imagem)


def update_image_table(df: pd.DataFrame) -> None:
    icerberg_imagem = IcebergFactory().load_iceberg_table(const.DATABASE, const.TABLE_IMAGEM, Imagem)
    pa_table_imagem = PATableImagem()
    pa_table_imagem.add_dataframe(df)
    icerberg_imagem.append(pa_table_imagem)


def count_dataset_pixels(ds: Dataset) -> int:
    spatial_dims = [d for d in ds['scl'].dims if d != 'time']
    n_pixels_por_t = 1
    for d in spatial_dims:
        n_pixels_por_t *= ds.sizes[d]
    return n_pixels_por_t

