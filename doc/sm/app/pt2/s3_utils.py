import boto3
import io
from PIL import Image

_s3 = boto3.client('s3')


def _parse_s3_uri(uri: str) -> tuple[str, str]:
    path = uri.removeprefix('s3://')
    bucket, _, key = path.partition('/')
    return bucket, key


def download_image(s3_uri: str) -> Image.Image:
    bucket, key = _parse_s3_uri(s3_uri)
    resp = _s3.get_object(Bucket=bucket, Key=key)
    return Image.open(io.BytesIO(resp['Body'].read())).convert('RGB')
