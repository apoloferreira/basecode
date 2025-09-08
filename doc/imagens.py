import sys
import os
import boto3
from datetime import datetime
from shapely.geometry import Polygon
from xarray import Dataset
from pystac_client import Client
from odc.stac import stac_load
from zarr.codecs.blosc import BloscCodec
from zarr.storage import ObjectStore
from obstore.store import S3Store

sys.path.append(os.getcwd())
import constantes as const


def get_glue_credentials():
    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()
    return {
        "access_key": credentials.access_key,
        "secret_key": credentials.secret_key,
        "token": credentials.token,
    }


def stac_search_images(polygon: Polygon, start_date: str) -> list:
    client = Client.open(const.STAC_CATALOG)

    end_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    search = client.search(
        collections=[const.SATELLITE_COLLECTION],
        datetime=f"{start_date}/{end_date}",
        bbox=polygon.bounds,
        sortby=[{"field": "properties.datetime", "direction": "asc"}],
    )

    items = list(search.items())
    # print(f"Found: {len(items):d} datasets")
    return items


def stac_load_dataset(polygon: Polygon, stac_metadata: list) -> Dataset:
    dataset = stac_load(
        stac_metadata,
        bands=(const.BANDS['constants'] + const.BANDS['categorical']),
        crs="utm",
        resolution=10,
        groupby="solar_day",
        bbox=polygon.bounds,
        nodata=0,
        chunks={"x": 2048, "y": 2048, "time": 1},
        resampling={**{n: "bilinear" for n in const.BANDS['constants']}, 
                    **{n: "nearest" for n in const.BANDS['categorical']}},
    )
    return dataset


def save_s3_zarr(ds: Dataset, id_poligono: str, mode: str, append_kwargs: dict):
    creds = get_glue_credentials()
    s3_store = S3Store(
        bucket=const.S3_BUCKET_IMAGENS,
        prefix=f"{const.S3_PREFIX_IMAGENS}/{const.SATELLITE_COLLECTION}/{id_poligono}.zarr",
        region=const.REGION,
        access_key_id=creds["access_key"],
        secret_access_key=creds["secret_key"],
        session_token=creds["token"],
    )
    zarr_store = ObjectStore(s3_store)
    compressor = BloscCodec(cname="lz4", clevel=5, shuffle="shuffle")
    encoding = {
        var: {
            "compressor": compressor,
            "shards": (1, 4096, 4096),
            "chunks": (1, 2048, 2048),
        }
        for var in ds.data_vars
    }
    ds.to_zarr(
        store=zarr_store,
        mode=mode,
        consolidated=True,
        encoding=encoding,
        write_empty_chunks=False,
        zarr_format=3,
        **append_kwargs
        # align_chunks=True,
    )


def s3_path_exists(bucket_name: str, s3_path: str) -> bool:
    client_s3 = boto3.client(service_name="s3", region_name="us-east-1")
    # Remove barra inicial, se existir
    s3_path = s3_path.lstrip("/")
    response = client_s3.list_objects_v2(
        Bucket=bucket_name,
        Prefix=s3_path,
        MaxKeys=1
    )
    return "Contents" in response
