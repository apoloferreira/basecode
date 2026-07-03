from __future__ import annotations
from typing import Any, Optional, Dict
from pydantic import BaseModel, Field


class ManifestItem(BaseModel):
    # Padrão comum do manifest do SageMaker
    source_ref: str = Field(..., alias="source-ref")
    id: Optional[str] = None
    extra: Dict[str, Any] = {}

    class Config:
        populate_by_name = True


class Prediction(BaseModel):
    id: Optional[str] = None
    source_ref: str = Field(..., alias="source-ref")
    pred: Any

    class Config:
        populate_by_name = True
