from __future__ import annotations

import io
import logging
import os
import time
import warnings

import boto3
import numpy as np
from botocore.exceptions import ClientError
from PIL import Image, UnidentifiedImageError

import triton_python_backend_utils as pb_utils

logger = logging.getLogger(__name__)

cleint_s3 = boto3.client("s3")

RESIZE = (256, 256)
MAX_BODY_BYTES = 10 * 1024 * 1024  # 10 MB — rejeita antes de decodificar

# Limite de pixels para evitar decompression bombs (ex: PNG 1px → ~4 GB descomprimido).
# 4096×4096 cobre imagens bem maiores que as 256×256 que usamos.
Image.MAX_IMAGE_PIXELS = 4096 * 4096
warnings.simplefilter("error", Image.DecompressionBombWarning)

# Allowlist de buckets: ALLOWED_S3_BUCKETS=bucket-a,bucket-b injetado pelo SageMaker.
# Se a variável estiver vazia, bloqueia tudo por segurança (fail-closed).
_RAW = os.environ.get("ALLOWED_S3_BUCKETS", "")
ALLOWED_BUCKETS: frozenset[str] = frozenset(b.strip() for b in _RAW.split(",") if b.strip())


class TritonPythonModel:

    def initialize(self, _args):
        if not ALLOWED_BUCKETS:
            logger.warning("ALLOWED_S3_BUCKETS não configurado — todas as requisições serão rejeitadas")

    def execute(self, requests):
        responses = []
        for request in requests:
            try:
                record_ids = pb_utils.get_input_tensor_by_name(request, "record_id").as_numpy()
                s3_paths = pb_utils.get_input_tensor_by_name(request, "image_s3_path").as_numpy()
                # record_ids / s3_paths shape: (batch_size, 1), dtype object (bytes)
                batch = []
                for i in range(len(s3_paths)):
                    t0 = time.perf_counter()
                    arr = _download_preprocess(s3_paths[i, 0].decode())
                    elapsed = time.perf_counter() - t0
                    rid = record_ids[i, 0].decode() if isinstance(record_ids[i, 0], bytes) else str(record_ids[i, 0])
                    logger.info("preprocess record_id=%s elapsed=%.4fs", rid, elapsed)
                    batch.append(arr)
                tensor = pb_utils.Tensor("preprocessed", np.stack(batch).astype(np.float32))
                responses.append(pb_utils.InferenceResponse(output_tensors=[tensor]))
            except _BucketNotAllowed:
                logger.warning("bucket não permitido", exc_info=True)
                responses.append(_error_response("invalid input"))
            except (Image.DecompressionBombWarning, Image.DecompressionBombError, _ImageTooLarge):
                logger.warning("imagem excede limite de tamanho", exc_info=True)
                responses.append(_error_response("image too large"))
            except (UnidentifiedImageError, OSError):
                logger.warning("imagem inválida ou corrompida", exc_info=True)
                responses.append(_error_response("invalid input"))
            except ClientError:
                logger.error("erro ao acessar S3", exc_info=True)
                responses.append(_error_response("upstream error"))
            except Exception:
                logger.error("erro inesperado no preprocess", exc_info=True)
                responses.append(_error_response("preprocessing failed"))
        return responses

    def finalize(self):
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _BucketNotAllowed(ValueError):
    pass


class _ImageTooLarge(ValueError):
    pass


def _error_response(msg: str) -> pb_utils.InferenceResponse:
    return pb_utils.InferenceResponse(output_tensors=[], error=pb_utils.TritonError(msg))


def _download_preprocess(s3_uri: str) -> np.ndarray:
    bucket, _, key = s3_uri.removeprefix("s3://").partition("/")

    if not bucket or not key:
        raise _BucketNotAllowed(bucket)
    if bucket not in ALLOWED_BUCKETS:
        raise _BucketNotAllowed(bucket)

    body = cleint_s3.get_object(Bucket=bucket, Key=key)["Body"].read(MAX_BODY_BYTES + 1)
    if len(body) > MAX_BODY_BYTES:
        raise _ImageTooLarge(f"{len(body)} bytes exceeds {MAX_BODY_BYTES}")

    img = Image.open(io.BytesIO(body)).convert("RGB").resize(RESIZE)
    arr = np.array(img, dtype=np.float32) / 255.0  # (H, W, C)
    return arr.transpose(2, 0, 1)                  # (C, H, W) = (3, 256, 256)
