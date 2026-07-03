from transformers import ViTForImageClassification


def build_model():
    return ViTForImageClassification.from_pretrained("google/vit-base-patch16-224-in21k")
