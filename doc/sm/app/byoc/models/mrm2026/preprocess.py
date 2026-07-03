from __future__ import annotations
from typing import Callable
from PIL import Image
import torch
from torchvision import transforms


def build_preprocess() -> Callable[[Image.Image], torch.Tensor]:
    # Ajuste conforme seu modelo
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        # transforms.Normalize(mean=(...), std=(...)),
    ])
