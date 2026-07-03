from PIL import Image

from torch import Tensor
from transformers import ViTFeatureExtractor


def preprocess_fn(images: Image.Image, return_tensors: str = "pt") -> Tensor:
    feature_extractor = ViTFeatureExtractor.from_pretrained("google/vit-base-patch16-224-in21k")
    return feature_extractor(images=images, return_tensors=return_tensors)
