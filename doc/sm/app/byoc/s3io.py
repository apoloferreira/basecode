from __future__ import annotations
import io
from typing import Tuple

import boto3
from botocore.config import Config
from PIL import Image

from .config import settings

boto_cfg = Config(
    read_timeout=settings.s3_read_timeout_sec,
    retries={"max_attempts": 10, "mode": "standard"}
)
s3 = boto3.client("s3", config=boto_cfg)


def parse_s3_uri(uri: str) -> Tuple[str, str]:
    if not uri.startswith("s3://"):
        raise ValueError(f"Invalid S3 URI: {uri}")
    bucket, key = uri[5:].split("/", 1)
    return bucket, key

def fetch_image(s3_uri: str) -> Image.Image:
    bucket, key = parse_s3_uri(s3_uri)
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = obj["Body"].read()
    return Image.open(io.BytesIO(data))  # .convert("RGB")
