import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Settings:
    # SageMaker coloca o model.tar.gz extraído aqui
    model_dir: str = os.getenv("SM_MODEL_DIR", "/opt/ml/model")

    # Ajustes de performance
    io_workers: int = int(os.getenv("IO_WORKERS", "16"))
    batch_size: int = int(os.getenv("BATCH_SIZE", "16"))
    max_payload_mb: int = int(os.getenv("SAGEMAKER_MAX_PAYLOAD_IN_MB", "6"))

    # timeouts/rede
    s3_read_timeout_sec: int = int(os.getenv("S3_READ_TIMEOUT_SEC", "60"))

    # logs
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


def compute_execution_parameters() -> dict[str, Any]:
    """
    Endpoint opcional: /execution-parameters.
    A AWS espera JSON com: MaxConcurrentTransforms, BatchStrategy, MaxPayloadInMB.
    (Use quando o cliente não setou esses valores no CreateTransformJob.)
    """
    # Heurística conservadora:
    # - Em GPU, "concorrência alta" (várias requisições simultâneas) costuma piorar;
    #   prefira MULTI_RECORD com batches maiores por request.
    # - Sem saber seu perfil, retornamos 1 por padrão e deixamos o ganho vir do MULTI_RECORD.
    cpu = os.cpu_count() or 1

    # Se você tiver certeza de CPU-only e inferência leve, pode aumentar:
    # max_concurrent = min(max(1, cpu // 2), 8)
    max_concurrent = 1

    # Se o usuário setar SAGEMAKER_MAX_PAYLOAD_IN_MB, respeite; senão default AWS (6)
    max_payload = os.getenv("SAGEMAKER_MAX_PAYLOAD_IN_MB")
    if max_payload is not None:
        try:
            max_payload_mb = int(max_payload)
        except ValueError:
            max_payload_mb = os.getenv("SAGEMAKER_MAX_PAYLOAD_IN_MB", "6")
    else:
        max_payload_mb = os.getenv("SAGEMAKER_MAX_PAYLOAD_IN_MB", "6")

    return {
        "MaxConcurrentTransforms": max_concurrent,
        "BatchStrategy": "MULTI_RECORD",
        "MaxPayloadInMB": max_payload_mb,
    }
