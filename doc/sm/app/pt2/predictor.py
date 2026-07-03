import torch
import torchvision.transforms as T
from pathlib import Path

import s3_utils

CLASSES = ['cardboard', 'glass', 'metal', 'paper', 'plastic', 'trash']
MODEL_PATH = Path('/opt/ml/model/ResNet18.pt2')


class Predictor:
    def __init__(self) -> None:
        self._device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self._transform = T.Compose([T.Resize((256, 256)), T.ToTensor()])
        self._model: torch.nn.Module | None = None

    def load(self) -> None:
        ep = torch.export.load(str(MODEL_PATH))
        # .eval() não é necessário: o estado de avaliação está baked no grafo exportado.
        self._model = ep.module().to(self._device)

    def is_ready(self) -> bool:
        return self._model is not None

    def predict(self, record: dict) -> dict:
        assert self._model is not None, "Model not loaded — call load() first"
        record_id = record['record_id']
        try:
            img = s3_utils.download_image(record['image_s3_path'])
            tensor = self._transform(img).unsqueeze(0).to(self._device)
            with torch.no_grad():
                scores = self._model(tensor)[0]  # [6]
            pred_idx = int(scores.argmax())
            score = float(scores[pred_idx])
            return {
                'record_id': record_id,
                'classe': CLASSES[pred_idx],
                'score': round(score, 4),
            }
        except Exception as e:
            return {
                'record_id': record_id,
                'classe': None,
                'score': None,
                'erro': str(e),
            }
