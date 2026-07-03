from __future__ import annotations

import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any

from fastapi import FastAPI, Request, Response, HTTPException, status

from .model_handler import ModelCatalog, ModelSpec, ModelRegistry
from .inference import parse_request_body, predict, encode_predictions
from .config import compute_execution_parameters


logger = logging.getLogger(__file__)

MODELS_ROOT = Path(__file__).resolve().parent / "models"
logger.info(f"Models root: {MODELS_ROOT}")

DEFAULT_MAX_PAYLOAD_MB = 6
BATCH_STRATEGY = os.getenv("SAGEMAKER_BATCH_STRATEGY", "MULTI_RECORD")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    catalog = ModelCatalog(MODELS_ROOT)
    catalog.scan()

    registry = ModelRegistry(catalog=catalog)
    registry.load("mrm_dsa")
    app.state.model: ModelSpec = registry.get("mrm_dsa")  # type: ignore[attr-defined]

    logger.info("Model loaded and ready.")
    yield
    logger.info("Shutting down application.")


app = FastAPI(lifespan=lifespan)


@app.get("/ping")
async def ping(request: Request) -> Response:
    """
    Healthcheck:
    - Deve retornar 200 e body vazio.
    - Pode ser usado para "warm-up" (carregar modelo).
    """
    model = getattr(request.app.state, "model", None)
    if model is None:
        return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    return Response(content=b"", media_type="text/plain", status_code=status.HTTP_200_OK)

@app.get("/models")
async def list_models() -> dict[str, Any]:
    catalog: ModelCatalog = app.state.catalog  # type: ignore[attr-defined]
    registry: ModelRegistry = app.state.registry  # type: ignore[attr-defined]
    return {"available": catalog.list_models(), "loaded": registry.list_loaded()}

@app.get("/execution-parameters")
def execution_parameters() -> dict[str, Any]:
    """
    Endpoint opcional do Batch Transform:
    Retorna tuning dinâmico: MaxConcurrentTransforms, BatchStrategy, MaxPayloadInMB.
    """
    return compute_execution_parameters()

@app.post("/invocations")
async def invocations(request: Request) -> Response:
    """
    Inference:
    - Recebe payload via HTTP.
    - Para JSON Lines MULTI_RECORD: várias linhas JSON no body.
    """
    content_type = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    # JSON Lines costuma vir como text/plain, application/jsonlines, application/jsonl etc.
    # Como é BYOC, aceite alguns tipos comuns.
    accepted = {
        "text/plain",
        "application/jsonlines",
        "application/jsonl",
        "application/x-ndjson",
        "application/json",
    }
    if content_type and content_type not in accepted:
        raise HTTPException(status_code=415, detail=f"Unsupported content-type: {content_type}")

    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Empty request body")

    model = getattr(request.app.state, "model", None)
    if model is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model not loaded")

    try:
        items = parse_request_body(body, content_type=content_type)
        preds = predict(model, items)
        out_bytes, out_ct = encode_predictions(preds)
        return Response(content=out_bytes, media_type=out_ct, status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.exception("Inference failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
