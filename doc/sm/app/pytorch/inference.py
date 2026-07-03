"""
SageMaker Script Mode — PyTorch DLC Inference Handler
Batch Transform com modelo ResNet18 carregado via state_dict (.pth).

Estrutura esperada no model.tar.gz:
  model.tar.gz
  ├── ResNet18.pth
  └── code/
      ├── inference.py      ← este arquivo
      ├── model.py          ← ResNet18Model (copiado de src/model.py)
      ├── s3_utils.py
      └── requirements.txt

Funções do SageMaker Serving (chamadas pelo DLC automaticamente):
  model_fn    → carregamento do modelo na inicialização do container
  input_fn    → deserialização do body HTTP recebido em /invocations
  predict_fn  → download S3 + pré-processamento + inferência
  output_fn   → serialização da resposta
"""
from __future__ import annotations

import sys
import json
import logging
from pathlib import Path

import torch
import torchvision.transforms as T

import s3_utils

logger = logging.getLogger(__name__)

CLASSES = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]

# Definido uma vez no módulo — sem estado, reutilizado em todas as requisições
_TRANSFORM = T.Compose([T.Resize((256, 256)), T.ToTensor()])


# ---------------------------------------------------------------------------
# model_fn — chamada UMA VEZ quando o container sobe
# ---------------------------------------------------------------------------

def model_fn(model_dir: str) -> dict:
    """
    Carrega ResNet18.pth via state_dict e devolve um contexto de inferência.

    O SageMaker passa /opt/ml/model/ como model_dir.
    O objeto retornado aqui é repassado como segundo argumento de predict_fn.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # model.py vive em code/ dentro do tar.gz → /opt/ml/model/code/
    code_dir = str(Path(model_dir) / "code")
    if code_dir not in sys.path:
        sys.path.insert(0, code_dir)

    from model import ResNet18Model  # noqa: PLC0415

    pth_path = Path(model_dir) / "ResNet18.pth"
    logger.info("Carregando %s no device %s", pth_path, device)
    model = ResNet18Model()
    model.load_state_dict(
        torch.load(pth_path, map_location=device, weights_only=True)
    )
    model.eval()
    model.to(device)
    logger.info("Modelo carregado com sucesso.")

    return {"model": model, "device": device}


# ---------------------------------------------------------------------------
# input_fn — chamada a cada requisição POST /invocations
# ---------------------------------------------------------------------------

def input_fn(request_body: str | bytes, content_type: str) -> list[dict]:
    """
    Deserializa o body JSONL recebido pelo SageMaker.

    Com BatchStrategy=SingleRecord: 1 linha por requisição.
    Com BatchStrategy=MultiRecord:  N linhas por requisição.
    Em ambos os casos retorna uma lista de dicts.
    """
    if isinstance(request_body, bytes):
        request_body = request_body.decode("utf-8")

    if content_type not in ("application/json", "application/jsonlines"):
        raise ValueError(f"Content-Type não suportado: {content_type}")

    lines = [ln for ln in request_body.strip().splitlines() if ln.strip()]
    return [json.loads(ln) for ln in lines]


# ---------------------------------------------------------------------------
# predict_fn — chamada a cada requisição com o output de input_fn
# ---------------------------------------------------------------------------

def predict_fn(data: list[dict], model_ctx: dict) -> list[dict]:
    """
    Executa download S3 + pré-processamento + inferência para cada registro.

    Retorna uma lista de dicts na mesma ordem dos registros de entrada.
    Erros por registro são capturados individualmente para não abortar o batch.
    """
    model = model_ctx["model"]
    device = model_ctx["device"]
    results = []

    for record in data:
        record_id = record.get("record_id", "")
        try:
            img = s3_utils.download_image(record["image_s3_path"])
            tensor = _TRANSFORM(img).unsqueeze(0).to(device)

            with torch.no_grad():
                scores = model(tensor)[0]  # shape: (6,)

            pred_idx = int(scores.argmax())
            results.append({
                "record_id": record_id,
                "class_name": CLASSES[pred_idx],
                "score": round(float(scores[pred_idx]), 6),
            })
        except Exception:
            logger.exception("Erro na inferência record_id=%s", record_id)
            results.append({
                "record_id": record_id,
                "class_name": None,
                "score": None,
            })

    return results


# ---------------------------------------------------------------------------
# output_fn — chamada com o output de predict_fn para serializar a resposta
# ---------------------------------------------------------------------------

def output_fn(prediction: list[dict], accept: str) -> tuple[str, str]:
    """
    Serializa a lista de resultados como JSONL.

    Retorna (body, content_type). O SageMaker usa o content_type como
    header Content-Type da resposta HTTP.
    """
    body = "\n".join(json.dumps(r, ensure_ascii=False) for r in prediction)
    return body, "application/jsonlines"
