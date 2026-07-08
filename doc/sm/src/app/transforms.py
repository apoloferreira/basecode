from typing import List
import torch
from PIL import Image
from torchvision.transforms import v2 as T


_IMAGENET_MEAN = [0.485, 0.456, 0.406]
_IMAGENET_STD = [0.229, 0.224, 0.225]


def build_transform(input_size: int = 224) -> T.Compose:
    return T.Compose([
        T.Lambda(lambda img: img.convert("RGB")),
        T.Resize((input_size, input_size), antialias=True),
        T.ToImage(),
        T.ToDtype(torch.float32, scale=True),
        T.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD),
    ])


def preprocess_batch(images: List[Image.Image], input_size: int = 224) -> torch.Tensor:
    transform = build_transform(input_size)
    tensors = [transform(img) for img in images]
    return torch.stack(tensors)
