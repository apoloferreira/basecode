from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Sequence, Any
from PIL import Image

import torch
from fastapi import HTTPException, status

from .config import settings
from .schemas import ManifestItem, Prediction
from .s3io import fetch_image
from .model_handler import ModelSpec

logger = logging.getLogger("app.inference")


def to_jsonlines(outputs: list[dict[str, Any]]) -> bytes:
    return ("\n".join(json.dumps(o, ensure_ascii=False) for o in outputs) + "\n").encode("utf-8")

def parse_jsonlines(raw: bytes) -> list[dict[str, Any]]:
    """
    MULTI_RECORD com SplitType=Line: o SageMaker concatena vários registros
    num único payload, separados por \n (JSON Lines).
    """
    # Remove whitespace no começo/fim e ignora linhas vazias
    text = raw.decode("utf-8", errors="strict")
    lines = [ln for ln in text.splitlines() if ln.strip()]

    records: list[dict[str, Any]] = []
    for i, ln in enumerate(lines):
        try:
            obj = json.loads(ln)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON on line {i}: {str(e)}"
            ) from e
        if not isinstance(obj, dict):
            # Se você quiser permitir arrays/strings, remova essa restrição.
            raise HTTPException(
                status_code=400,
                detail=f"Each JSON Lines record must be an object/dict. Line {i} is {type(obj).__name__}."
            )
        records.append(obj)

    return records

def parse_request_body(body: bytes | str, content_type: str) -> list[ManifestItem]:
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")

    logger.debug(f"Parsing request body with Content-Type: {content_type}")
    ct = content_type.split(";")[0].strip().lower()
    if ct not in ("application/jsonlines", "application/json", "text/plain", ""):
        raise ValueError(f"Unsupported Content-Type: {content_type}")

    text = body.strip() # type: ignore
    if not text:
        return []

    # JSON Lines (1+ linhas)
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) == 1 and ct == "application/json":
        # JSON único
        obj = json.loads(lines[0])
        return [ManifestItem.model_validate(obj)]
    else:
        return [ManifestItem.model_validate(json.loads(ln)) for ln in lines]

def encode_predictions(preds: Sequence[Prediction]) -> tuple[bytes, str]:
    # Para Batch Transform, JSONLines é ótimo
    out = "\n".join(p.model_dump_json(by_alias=True) for p in preds) + "\n"
    return out.encode("utf-8"), "application/jsonlines"

def fetch_one(item: ManifestItem) -> tuple[ManifestItem, Image.Image]:
    img = fetch_image(item.source_ref)
    return item, img

@torch.inference_mode()
def predict(bundle: ModelSpec, items: list[ManifestItem]) -> list[Prediction]:
    if not items:
        return []

    model = bundle.module
    device = bundle.device
    preprocess = bundle.preprocess

    io_workers = settings.io_workers
    batch_size = settings.batch_size

    # 1) Download+decode paralelo
    decoded: list[tuple[ManifestItem, Image.Image]] = []
    with ThreadPoolExecutor(max_workers=io_workers) as ex:
        futs = [ex.submit(fetch_one, it) for it in items]
        for fut in as_completed(futs):
            decoded.append(fut.result())

    # 2) preprocess CPU
    tensors: list[torch.Tensor] = []
    metas: list[ManifestItem] = []
    for meta, img in decoded:
        img_processed = preprocess(img)
        tensors.append(img_processed)
        metas.append(meta)

    # 3) mini-batches na GPU
    preds_out: list[Prediction] = []
    for i in range(0, len(tensors), batch_size):
        batch = torch.stack(tensors[i:i + batch_size], dim=0).to(device, non_blocking=True)
        logits = model(batch)
        pred_ids = torch.argmax(logits, dim=1).detach().cpu().tolist()

        # Especifico para modelo da DSA
        mapeamento_classe = {
            "angular_leaf_spot": 0,
            "bean_rust": 1,
            "healthy": 2,
        }
        reverse_mapping = {v: k for k, v in mapeamento_classe.items()}
        pred_classes = [reverse_mapping.get(valor) for valor in pred_ids]

        for j, pred in enumerate(pred_classes):
            meta = metas[i + j]
            preds_out.append(
                Prediction(
                    id=meta.id,
                    **{"source-ref": meta.source_ref},
                    pred=pred  # int(pred),
                )
            )

    return preds_out
