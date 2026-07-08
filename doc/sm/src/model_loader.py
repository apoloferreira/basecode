import time
from pathlib import Path

import torch

from src.logger import get_logger

logger = get_logger(__name__)


class ModelLoader:

    def __init__(self, model_path: str, use_half_precision: bool, device: str):
        self.model_path = model_path
        self.use_half_precision = use_half_precision
        self.device = device
        self.model: torch.nn.Module | None = None
        self.ready: bool = False

    def load(self) -> None:
        path = Path(self.model_path)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        t0 = time.perf_counter()
        try:
            model = torch.jit.load(str(path), map_location=self.device)
            model_type = "torchscript"
            model = torch.jit.optimize_for_inference(model)
        except Exception:
            model = torch.load(str(path), map_location=self.device, weights_only=False)
            model_type = "eager"

        model.train(False)   # modo inferencia

        if self.use_half_precision:
            model = model.half()

        self.model = model
        self.ready = True
        elapsed_ms = round((time.perf_counter() - t0) * 1000)
        logger.info(
            msg="Model loaded",
            extra={"load_time_ms": elapsed_ms, "model_type": model_type, "device": self.device},
        )
