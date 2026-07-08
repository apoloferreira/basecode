import io
import json
import time
from typing import List

import torch
from PIL import Image, UnidentifiedImageError

from src.app.transforms import preprocess_batch
from src.logger import get_logger

logger = get_logger(__name__)


class InferenceHandler:

    def __init__(
        self,
        model: torch.nn.Module,
        input_size: int,
        use_half_precision: bool,
        device: str,
    ):
        self.model = model
        self.input_size = input_size
        self.use_half_precision = use_half_precision
        self.device = device

    def _decode(self, raw_images: List[bytes]) -> List[Image.Image]:
        decoded = []
        for idx, raw in enumerate(raw_images):
            try:
                img = Image.open(io.BytesIO(raw))
                img.load()
                decoded.append(img)
            except (UnidentifiedImageError, Exception) as exc:
                raise ValueError(f"Failed to decode image at index {idx}: {exc}") from exc
        return decoded

    def run(self, raw_images: List[bytes]) -> List[dict]:
        t0 = time.perf_counter()
        pil_images = self._decode(raw_images)
        batch = preprocess_batch(pil_images, self.input_size)

        if self.use_half_precision:
            batch = batch.half()
        batch = batch.to(self.device)

        with torch.no_grad():
            if self.use_half_precision and self.device.startswith("cuda"):
                with torch.amp.autocast("cuda"):
                    logits = self.model(batch)
            else:
                logits = self.model(batch)

        probs = torch.softmax(logits.float(), dim=1).cpu().tolist()
        elapsed_ms = round((time.perf_counter() - t0) * 1000)

        results = [
            {
                "file_index": i,
                "predictions": pred,
                "label_idx": int(max(range(len(pred)), key=pred.__getitem__)),
            }
            for i, pred in enumerate(probs)
        ]

        logger.info(
            msg="Inference completed",
            extra={"batch_size": len(raw_images), "inference_time_ms": elapsed_ms},
        )
        return results

    def serialize_jsonl(self, results: List[dict]) -> str:
        return "\n".join(json.dumps(r) for r in results) + "\n"
